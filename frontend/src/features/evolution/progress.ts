export const PROGRESS_KEY='fieldtofit:evolution:reading:v1';
export type RecordEntry={read:boolean;revision:number;at:string};
export type Records=Record<string,RecordEntry>;
export type ReadStatus='unread'|'read'|'updated';
export function decodeProgress(value:string|null):Records {
  if(!value)return {};
  const raw=JSON.parse(value);
  if(raw?.version!==1||!raw.records||typeof raw.records!=='object'||Array.isArray(raw.records))throw Error('Invalid reading record');
  const records:Records={};
  for(const [id,v] of Object.entries(raw.records)){
    const item=v as RecordEntry;
    if(/^[TIS]\d{2}$/.test(id)&&typeof item?.read==='boolean'&&Number.isInteger(item.revision)&&item.revision>0&&typeof item.at==='string'&&Number.isFinite(Date.parse(item.at)))records[id]={read:item.read,revision:item.revision,at:item.at};
  }
  return records;
}
export function statusFor(records:Records,id:string,revision:number):ReadStatus {
  const record=records[id];return !record?.read?'unread':record.revision<revision?'updated':'read';
}
export function chooseQuestion<T extends {id:string;revision:number}>(questions:T[],records:Records,current='',random=Math.random):T|undefined {
  const pending=questions.filter(q=>statusFor(records,q.id,q.revision)!=='read');
  const pool=pending.length?pending:questions;
  const different=pool.filter(q=>q.id!==current),candidates=different.length?different:pool;
  return candidates[Math.min(candidates.length-1,Math.max(0,Math.floor(random()*candidates.length)))];
}
