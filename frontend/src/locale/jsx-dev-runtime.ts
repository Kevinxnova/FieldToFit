import { jsxDEV as original } from 'react/jsx-dev-runtime';
import { jsx, Fragment } from './jsx-runtime';
export { Fragment };
export type { JSX } from 'react';
export const jsxDEV:typeof original = (type,props,key) => jsx(type,props,key);
