import { vertex, fragment, overlayVertex, overlayFragment, textVertex, textFragment } from './forYouShaders';
import { createSphereFlow } from './sphereFlow';

/** Optional WebGL scene: owns its listeners, animation and GPU resources. */
export function mountForYouScene(art: HTMLDivElement, canvas: HTMLCanvasElement, globe: HTMLButtonElement): () => void {
  const context = canvas.getContext('webgl2', { alpha: false, antialias: false, powerPreference: 'default' });
  if (!context) return () => {};
  const gl = context;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const events = new AbortController();
  const resources = { programs: [] as WebGLProgram[], textures: [] as WebGLTexture[], buffers: [] as WebGLBuffer[], vaos: [] as WebGLVertexArrayObject[] };
  const locations = new Map<WebGLProgram, Map<string, WebGLUniformLocation | null>>();
  const images: HTMLImageElement[] = [];
  const flow = createSphereFlow();
  const pulses: number[] = [], brush: { x: number; y: number; t: number }[] = [];
  let generation = 0;
  let disposed = false, ready = false, inView = true, raf = 0, time = 0, last = 0, lastPaint = -100;
  let touch: { x: number; y: number; t: number } | null = null;
  let previous: { u: number; v: number } | null = null;
  const view = { width: 1, height: 1, scale: 1, left: 0, top: 0 };
  let main: WebGLProgram, shell: WebGLProgram, words: WebGLProgram;
  let quadVAO: WebGLVertexArrayObject, shellVAO: WebGLVertexArrayObject, textVAO: WebGLVertexArrayObject;
  let textures: WebGLTexture[], letterTexture: WebGLTexture, dyeTexture: WebGLTexture;
  const ages = new Float32Array(3), marks = new Float32Array(72);
  const uniform = (program: WebGLProgram, name: string) => {
    let cache = locations.get(program);
    if (!cache) { cache = new Map(); locations.set(program, cache); }
    if (!cache.has(name)) cache.set(name, gl.getUniformLocation(program, name));
    return cache.get(name)!;
  };
  function releaseGPU() {
    resources.programs.forEach(p => gl.deleteProgram(p)); resources.programs.length = 0;
    resources.textures.forEach(t => gl.deleteTexture(t)); resources.textures.length = 0;
    resources.buffers.forEach(b => gl.deleteBuffer(b)); resources.buffers.length = 0;
    resources.vaos.forEach(v => gl.deleteVertexArray(v)); resources.vaos.length = 0;
    locations.clear();
  }
  function fallback() {
    generation++; ready = false; cancelAnimationFrame(raf); raf = 0;
    delete art.dataset.renderer; globe.disabled = true;
  }
  function compile(kind: number, source: string) {
    const shader = gl.createShader(kind);
    if (!shader) throw new Error('Shader unavailable');
    gl.shaderSource(shader, source); gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) { gl.deleteShader(shader); throw new Error('Shader compilation failed'); }
    return shader;
  }
  function program(v: string, f: string) {
    const p = gl.createProgram(); if (!p) throw new Error('Program unavailable');
    resources.programs.push(p);
    const vs = compile(gl.VERTEX_SHADER, v);
    let fs: WebGLShader | undefined;
    try { fs = compile(gl.FRAGMENT_SHADER, f); gl.attachShader(p, vs); gl.attachShader(p, fs); gl.linkProgram(p); }
    finally { gl.deleteShader(vs); if (fs) gl.deleteShader(fs); }
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error('Program linking failed');
    return p;
  }
  function vao(program: WebGLProgram, name: string, data: number[], size: number) {
    const v = gl.createVertexArray(), buffer = gl.createBuffer();
    if (v) resources.vaos.push(v); if (buffer) resources.buffers.push(buffer);
    if (!v || !buffer) throw new Error('Geometry unavailable');
    gl.bindVertexArray(v); gl.bindBuffer(gl.ARRAY_BUFFER, buffer); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(data), gl.STATIC_DRAW);
    const attr = gl.getAttribLocation(program, name); gl.enableVertexAttribArray(attr); gl.vertexAttribPointer(attr, size, gl.FLOAT, false, 0, 0);
    return v;
  }
  function texture(image?: TexImageSource, repeat = false) {
    const t = gl.createTexture(); if (!t) throw new Error('Texture unavailable');
    resources.textures.push(t); gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, repeat ? gl.REPEAT : gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    if (image) gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
    return t;
  }
  function load(path: string): Promise<HTMLImageElement> {
    return new Promise((resolve, reject) => {
      const image = new Image(); images.push(image);
      image.onload = () => { image.onload = image.onerror = null; resolve(image); };
      image.onerror = () => { image.onload = image.onerror = null; reject(new Error('Scene asset unavailable')); };
      image.src = '/assets/for-you-scene/' + path;
    });
  }
  function use(program: WebGLProgram) {
    gl.useProgram(program); gl.uniform2f(uniform(program, 'resolution'), canvas.width, canvas.height);
    const dpr = canvas.width / view.width;
    gl.uniform3f(uniform(program, 'frame'), view.scale * dpr, view.left * dpr, view.top * dpr); gl.uniform1f(uniform(program, 'seconds'), time);
  }
  function render() {
    if (!ready || disposed) return;
    gl.viewport(0, 0, canvas.width, canvas.height); gl.disable(gl.BLEND); use(main);
    textures.forEach((t, i) => { gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, t); });
    gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, dyeTexture);
    ['bg', 'planet', 'geometry', 'dye'].forEach((name, i) => gl.uniform1i(uniform(main, name), i));
    ages.fill(-1); pulses.forEach((t, i) => { ages[i] = time - t < 5 ? time - t : -1; }); gl.uniform1fv(uniform(main, 'pulses[0]'), ages);
    marks.fill(0); brush.forEach((b, i) => { marks[i * 3] = b.x; marks[i * 3 + 1] = b.y; marks[i * 3 + 2] = Math.exp(-(time - b.t) * 2.3); });
    gl.uniform3fv(uniform(main, 'brushes[0]'), marks); gl.bindVertexArray(quadVAO); gl.drawArrays(gl.TRIANGLES, 0, 3);
    gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); use(shell); gl.bindVertexArray(shellVAO); gl.drawArrays(gl.POINTS, 0, 9000);
    use(words); gl.activeTexture(gl.TEXTURE4); gl.bindTexture(gl.TEXTURE_2D, letterTexture); gl.uniform1i(uniform(words, 'letters'), 4);
    gl.bindVertexArray(textVAO); gl.drawArrays(gl.TRIANGLES, 0, 2400); gl.disable(gl.BLEND);
  }
  function resize() {
    const rect = art.getBoundingClientRect(); if (!rect.width || !rect.height || disposed) return;
    view.width = rect.width; view.height = rect.height;
    // Match the CSS container query: sidebar width must not shrink the scene.
    const mobile = rect.width <= 700;
    view.scale = mobile ? Math.max(rect.width / 1672, rect.height / 941) : Math.max(rect.width * .98 / 1672, rect.height / 941);
    view.left = mobile ? (rect.width - 1672 * view.scale) * .497 : rect.width * .697 - 830.7 * view.scale; view.top = (rect.height - 941 * view.scale) * .5;
    Object.assign(globe.style, { left: (view.left + 621 * view.scale) + 'px', top: (view.top + 239.6 * view.scale) + 'px', width: (419.4 * view.scale) + 'px', height: (419.4 * view.scale) + 'px' });
    const dpr = Math.min(devicePixelRatio || 1, 1.5);
    canvas.width = Math.round(rect.width * dpr); canvas.height = Math.round(rect.height * dpr); render();
  }
  function tick(now: number) {
    raf = 0; if (disposed || reduce.matches || !inView || document.hidden || !ready) return;
    if (now - last < 30) { raf = requestAnimationFrame(tick); return; }
    const dt = Math.min((now - last) / 1000, .04); last = now; time += dt;
    if (time - lastPaint < 12) {
      flow.step(dt); gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, dyeTexture);
      gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, flow.width, flow.height, gl.RGBA, gl.UNSIGNED_BYTE, flow.pixels);
    }
    render(); raf = requestAnimationFrame(tick);
  }
  function update() {
    cancelAnimationFrame(raf); raf = 0; globe.disabled = !ready || reduce.matches;
    if (disposed) return;
    if (ready && !reduce.matches && inView && !document.hidden) { last = performance.now(); raf = requestAnimationFrame(tick); } else render();
  }
  function move(event: PointerEvent) {
    if (disposed || reduce.matches || !ready || !inView) return;
    if (event.pointerType !== 'mouse' && touch && Math.abs(event.clientY - touch.y) > Math.abs(event.clientX - touch.x) + 7) return;
    const rect = art.getBoundingClientRect(), px = (event.clientX - rect.left - view.left) / view.scale, py = (event.clientY - rect.top - view.top) / view.scale;
    brush.push({ x: px, y: py, t: time }); if (brush.length > 24) brush.shift();
    const x = (px - 830.7) / (209.7 * .895), y = -(py - 449.3) / (209.7 * .895), rr = x * x + y * y;
    if (rr >= .98) { previous = null; return; }
    const z = Math.sqrt(1 - rr), a = .41, b = time * .0314159, kx = x * Math.cos(a) + y * Math.sin(a), ky = -x * Math.sin(a) + y * Math.cos(a);
    const nx = kx * Math.cos(b) + z * Math.sin(b), nz = -kx * Math.sin(b) + z * Math.cos(b), u = Math.atan2(nx, nz) / (2 * Math.PI) + .5, v = Math.asin(ky) / Math.PI + .5;
    let du = previous ? u - previous.u : 0; du -= Math.round(du); const dv = previous ? v - previous.v : 0;
    flow.splat(u, v, Math.max(-50, Math.min(50, du * 2200)), Math.max(-50, Math.min(50, dv * 1400))); lastPaint = time; previous = { u, v };
  }
  function pulse() {
    if (!ready || reduce.matches || disposed) return;
    pulses.push(time); if (pulses.length > 3) pulses.shift();
    for (let i = 0; i < 12; i++) flow.splat(i / 12, .19, Math.sin(i) * 6, 14); lastPaint = time;
  }
  art.addEventListener('pointermove', move, { passive: true, signal: events.signal });
  art.addEventListener('pointerdown', e => {
    if (e.pointerType !== 'mouse') touch = { x: e.clientX, y: e.clientY, t: performance.now() };
    move(e);
    if (e.pointerType === 'mouse' && e.target !== globe) pulse();
  }, { passive: true, signal: events.signal });
  art.addEventListener('pointerup', e => {
    if (e.pointerType !== 'mouse' && e.target !== globe && touch && performance.now() - touch.t < 350 && Math.hypot(e.clientX - touch.x, e.clientY - touch.y) < 12) pulse();
    touch = null;
  }, { passive: true, signal: events.signal });
  art.addEventListener('pointerleave', () => { previous = null; touch = null; }, { signal: events.signal });
  art.addEventListener('pointercancel', () => { previous = null; touch = null; }, { signal: events.signal });
  globe.addEventListener('click', pulse, { signal: events.signal });
  document.addEventListener('visibilitychange', update, { signal: events.signal });
  reduce.addEventListener('change', update, { signal: events.signal });
  const resizeObserver = new ResizeObserver(resize); resizeObserver.observe(art);
  const visibility = new IntersectionObserver(entries => { inView = entries[0].isIntersecting; update(); }, { threshold: .02 }); visibility.observe(art);
  canvas.addEventListener('webglcontextlost', e => { e.preventDefault(); fallback(); }, { signal: events.signal });
  canvas.addEventListener('webglcontextrestored', () => { if (!disposed) { releaseGPU(); initialize(); } }, { signal: events.signal });
  function initialize() {
    const loadGeneration = ++generation;
    void Promise.all(['city.avif', 'surface.webp', 'geometry.webp'].map(load)).then(loaded => {
      if (disposed || loadGeneration !== generation || gl.isContextLost()) return;
      main = program(vertex, fragment); shell = program(overlayVertex, overlayFragment); words = program(textVertex, textFragment);
      quadVAO = vao(main, 'aPosition', [-1, -1, 3, -1, -1, 3], 2);
      const points: number[] = []; for (let i = 0; i < 9000; i++) { const y = 1 - 2 * (i + .5) / 9000, r = Math.sqrt(1 - y * y), a = i * 2.39996323; points.push(r * Math.cos(a), y, r * Math.sin(a)); }
      shellVAO = vao(shell, 'position', points, 3);
      const ribbon: number[] = []; for (let i = 0; i < 400; i++) { const x = i / 400, z = (i + 1) / 400; ribbon.push(x, -1, z, -1, x, 1, z, -1, z, 1, x, 1); }
      textVAO = vao(words, 'ribbon', ribbon, 2); textures = loaded.map((image, i) => texture(image, i === 1));
      const label = document.createElement('canvas'); label.width = 1536; label.height = 160;
      const ctx = label.getContext('2d'); if (!ctx) throw new Error('Lettering unavailable');
      ctx.font = '600 120px Arial, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      const text = 'FIELD TO FIT · AI IN FOCUS'; ctx.translate(768, 80); ctx.scale(1420 / ctx.measureText(text).width, 1);
      ctx.fillStyle = '#ffffff'; ctx.shadowColor = '#8dffed'; ctx.shadowBlur = 7; ctx.fillText(text, 0, 4); ctx.shadowBlur = 0; ctx.fillText(text, 0, 4); letterTexture = texture(label, true);
      gl.activeTexture(gl.TEXTURE3); dyeTexture = texture(undefined, true);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, flow.width, flow.height, 0, gl.RGBA, gl.UNSIGNED_BYTE, flow.pixels);
      ready = true; resize(); art.dataset.renderer = 'webgl2'; update();
    }).catch(() => { if (!disposed && loadGeneration === generation) { fallback(); releaseGPU(); } });
  }
  initialize();
  return () => {
    disposed = true; fallback(); events.abort(); resizeObserver.disconnect(); visibility.disconnect();
    images.forEach(image => { image.onload = image.onerror = null; }); releaseGPU();
  };
}
