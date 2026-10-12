import { useEffect, useRef } from 'react';

/** Keep the hit area still while the inner card tilts; never animate touch scrolling. */
export function useHotCardMotion() {
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    const shell = ref.current;
    const foil = shell?.querySelector<HTMLElement>('.hot-card-foil');
    if (!shell || !foil) return;
    const fine = matchMedia('(hover: hover) and (pointer: fine)');
    const reduced = matchMedia('(prefers-reduced-motion: reduce)');
    let frame = 0;
    let target = { x: .5, y: .5 };
    let current = { ...target };
    const reset = () => {
      cancelAnimationFrame(frame);
      frame = 0;
      current = target = { x: .5, y: .5 };
      delete shell.dataset.tilting;
      for (const name of ['--card-rx', '--card-ry', '--card-x', '--card-y']) foil.style.removeProperty(name);
    };
    const draw = () => {
      current.x += (target.x - current.x) * .24;
      current.y += (target.y - current.y) * .24;
      foil.style.setProperty('--card-rx', `${-(current.y - .5) * 16}deg`);
      foil.style.setProperty('--card-ry', `${(current.x - .5) * 16}deg`);
      foil.style.setProperty('--card-x', `${current.x * 100}%`);
      foil.style.setProperty('--card-y', `${current.y * 100}%`);
      frame = Math.abs(target.x - current.x) + Math.abs(target.y - current.y) > .001
        ? requestAnimationFrame(draw) : 0;
    };
    const move = (event: PointerEvent) => {
      if (event.pointerType !== 'mouse' || event.buttons || !fine.matches || reduced.matches) {
        reset();
        return;
      }
      const box = shell.getBoundingClientRect();
      if (!box.width || !box.height) return;
      target = {
        x: Math.max(0, Math.min(1, (event.clientX - box.left) / box.width)),
        y: Math.max(0, Math.min(1, (event.clientY - box.top) / box.height)),
      };
      shell.dataset.tilting = 'true';
      if (!frame) frame = requestAnimationFrame(draw);
    };
    shell.addEventListener('pointermove', move, { passive: true });
    for (const event of ['pointerleave', 'pointercancel', 'pointerdown', 'focusin']) shell.addEventListener(event, reset);
    fine.addEventListener('change', reset);
    reduced.addEventListener('change', reset);
    window.addEventListener('blur', reset);
    document.addEventListener('visibilitychange', reset);
    return () => {
      reset();
      shell.removeEventListener('pointermove', move);
      for (const event of ['pointerleave', 'pointercancel', 'pointerdown', 'focusin']) shell.removeEventListener(event, reset);
      fine.removeEventListener('change', reset);
      reduced.removeEventListener('change', reset);
      window.removeEventListener('blur', reset);
      document.removeEventListener('visibilitychange', reset);
    };
  }, []);
  return ref;
}
