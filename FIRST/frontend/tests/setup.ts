import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { beforeEach, afterEach, vi } from 'vitest';
afterEach(()=>{cleanup();vi.restoreAllMocks();vi.unstubAllGlobals();});

function storage():Storage {const data=new Map<string,string>();return {get length(){return data.size;},key:index=>Array.from(data.keys())[index]??null,getItem:key=>data.get(key)??null,setItem:(key,value)=>{data.set(key,String(value));},removeItem:key=>{data.delete(key);},clear:()=>data.clear()};}
beforeEach(()=>{vi.stubEnv('NEXT_PUBLIC_API_URL','https://api.first.test');vi.stubGlobal('localStorage',storage());vi.stubGlobal('sessionStorage',storage());});
