/** Translate authored display text without mutating DOM, form data, IDs or evidence. */
import { createContext, useContext, createElement, type ReactNode } from 'react';
import { jsx as reactJSX, jsxs as reactJSXs, Fragment } from 'react/jsx-runtime';
import { english, languagePath, useLanguage } from './language';
export { Fragment };
export type { JSX } from 'react';
const Original = createContext(false);
const DISPLAY = ['title','alt','placeholder','aria-label','aria-description'];
export function DisplayText({children}:{children:ReactNode}) {
  const language=useLanguage();const original=useContext(Original);
  return typeof children==='string' && language==='en' && !original ? english(children) : children;
}
function Native({tag,elementProps}:{tag:string;elementProps:Record<string,any>}) {
  const language=useLanguage();const inherited=useContext(Original);
  const original=inherited || !!elementProps['data-original-language'] || /^zh/.test(elementProps.lang || '');
  const props={...elementProps};
  if (language==='en' && !original) {
    for (const name of DISPLAY) if (typeof props[name]==='string') props[name]=english(props[name]);
    if (tag==='a' && typeof props.href==='string' && /^\/(?:en\/)?(?:for-you|for-your-ai|news|watch|maps|sources|about|community|admin|feedback|collection)(?:[/?#]|$)/.test(props.href)) props.href=languagePath(props.href);
    const translate = (child:any):any => typeof child==='string' ? english(child) : Array.isArray(child) ? child.map(translate) : child;
    // Controlled inputs and explicitly attributed original evidence remain verbatim.
    if (!['textarea','input','script','style'].includes(tag)) props.children=translate(props.children);
  }
  const element=createElement(tag,props);
  return original!==inherited ? createElement(Original.Provider,{value:original},element) : element;
}
export const jsx:typeof reactJSX = (type,props,key) => typeof type==='string' ? reactJSX(Native,{tag:type,elementProps:props},key) : reactJSX(type,props,key);
export const jsxs:typeof reactJSXs = (type,props,key) => typeof type==='string' ? reactJSXs(Native,{tag:type,elementProps:props},key) : reactJSXs(type,props,key);
