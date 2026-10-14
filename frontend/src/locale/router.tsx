import { saveReadingPosition } from '../components/workspace/readingPosition';
import { Link as BaseLink, NavLink as BaseNavLink, Navigate as BaseNavigate, Routes as BaseRoutes, useLocation as baseLocation, useNavigate as baseNavigate, useSearchParams as baseSearchParams, createSearchParams, type URLSearchParamsInit, type NavigateOptions, type LinkProps, type NavLinkProps, type NavigateProps, type RoutesProps, type To, type NavigateFunction } from 'react-router';
import { canonicalPath, languagePath, useLanguage } from './language';
import { DisplayText } from './jsx-runtime';
export * from 'react-router';
function toLocale(to:To) { return typeof to==='string' ? languagePath(to) : {...to, ...(to.pathname ? {pathname:languagePath(to.pathname)} : {})}; }
export function Link(props:LinkProps) {
  useLanguage();const source=baseLocation();
  const destination=typeof props.to==='string'?props.to:props.to.pathname||'';
  const detail=/^\/(?:en\/)?(?:news\/|watch\/|maps(?:\/|$))/.test(destination);
  const fromHome=canonicalPath(source.pathname)==='/for-you';
  const returning=/^\/(?:en\/)?for-you(?:#technical-evolution-maps)?$/.test(destination)||!!props.state?.readingRestore||!!props.state?.restoreReading;
  const remembered=source.state?.readingReturn;
  const to=returning&&remembered?.url&&/^\/(?:en\/)?for-you(?:[?#]|$)/.test(remembered.url)?remembered.url:props.to;
  const state=fromHome&&detail?{...props.state,readingReturn:{url:source.pathname+source.search+source.hash,id:props.state?.readingReturn?.id},restoreReading:false}:returning&&remembered?{...props.state,restoreReading:true}:detail&&remembered?{readingReturn:remembered,...props.state}:props.state;
  return <BaseLink {...props} state={state} to={toLocale(to)} onClick={event=>{props.onClick?.(event);if(!event.defaultPrevented)saveReadingPosition(source.pathname+source.search,true);}}><DisplayText>{props.children}</DisplayText></BaseLink>;
}
export function NavLink(props:NavLinkProps) { useLanguage();return <BaseNavLink {...props} to={toLocale(props.to)}>{typeof props.children==='function' ? props.children : <DisplayText>{props.children}</DisplayText>}</BaseNavLink>; }
export function Navigate(props:NavigateProps) { useLanguage();return <BaseNavigate {...props} to={toLocale(props.to)}/>; }
export function useLocation() { const location=baseLocation();return {...location,pathname:canonicalPath(location.pathname)}; }
export function Routes(props:RoutesProps) { const location=useLocation();return <BaseRoutes {...props} location={location}/>; }
export function useNavigate():NavigateFunction { const navigate=baseNavigate();useLanguage();return ((to:To|number,options?:any) => typeof to==='number' ? navigate(to) : navigate(toLocale(to),options)) as NavigateFunction; }
export function useSearchParams(defaultInit?:URLSearchParamsInit):[URLSearchParams,(next:URLSearchParamsInit|((previous:URLSearchParams)=>URLSearchParamsInit),options?:NavigateOptions)=>void] {
  const [params]=baseSearchParams(defaultInit);const navigate=useNavigate();const location=useLocation();
  return [params,(next,options)=>navigate(location.pathname+'?'+createSearchParams(typeof next==='function'?next(params):next).toString()+location.hash,options)];
}
