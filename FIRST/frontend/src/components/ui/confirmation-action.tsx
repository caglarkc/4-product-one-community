'use client';
import {useEffect,useId,useRef,useState,type ComponentProps} from 'react';
import {Alert,Button,Checkbox} from './index';

type ConfirmationActionProps={
 actionKey:string;
 label:string;
 title:string;
 description:string;
 confirmationLabel:string;
 variant?:ComponentProps<typeof Button>['variant'];
 disabled?:boolean;
 busy?:boolean;
 onConfirm:()=>Promise<void>;
};

export function ConfirmationAction(props:ConfirmationActionProps){
 // A changed target, consequence or reason requires a fresh, explicit confirmation.
 return <ConfirmationActionContent key={JSON.stringify([props.actionKey,props.title,props.description,props.confirmationLabel])} {...props}/>;
}

function ConfirmationActionContent({label,title,description,confirmationLabel,variant='danger',disabled=false,busy=false,onConfirm}:ConfirmationActionProps){
 const [open,setOpen]=useState(false),[confirmed,setConfirmed]=useState(false),[pending,setPending]=useState(false),[error,setError]=useState('');
 const id=useId(),trigger=useRef<HTMLButtonElement>(null),group=useRef<HTMLDivElement>(null),lock=useRef(false),alive=useRef(true),returnFocus=useRef(false);
 useEffect(()=>{alive.current=true;return()=>{alive.current=false;};},[]);
 useEffect(()=>{
  if(open&&!pending&&!busy&&!disabled)group.current?.querySelector<HTMLInputElement>('input[type="checkbox"]')?.focus();
  else if(!open&&!pending&&!busy&&!disabled&&returnFocus.current){returnFocus.current=false;trigger.current?.focus();}
 },[open,pending,busy,disabled]);
 const blocked=disabled||busy||pending;
 function cancel(){if(blocked)return;returnFocus.current=true;setOpen(false);setConfirmed(false);setError('');}
 async function confirm(){
  if(blocked||!open||!confirmed||lock.current)return;
  lock.current=true;setPending(true);setError('');
  try{await onConfirm();if(alive.current){returnFocus.current=true;setOpen(false);setConfirmed(false);}}
  catch(caught){if(alive.current){setConfirmed(false);setError(caught instanceof Error?caught.message:'İşlem tamamlanamadı.');}}
  finally{lock.current=false;if(alive.current)setPending(false);}
 }
 return <div className="extension-stack">
  <Button ref={trigger} variant={variant} disabled={blocked} aria-expanded={open} aria-controls={`${id}-confirmation`} onClick={()=>{if(open)cancel();else{setConfirmed(false);setError('');setOpen(true);}}}>{label}</Button>
  {open&&<div ref={group} id={`${id}-confirmation`} role="group" aria-labelledby={`${id}-title`} aria-describedby={`${id}-description`} onKeyDown={event=>{if(event.key==='Escape'&&!blocked){event.preventDefault();event.stopPropagation();cancel();}}}>
   <p id={`${id}-title`} className="project-text"><strong>{title}</strong></p>
   <p id={`${id}-description`} className="project-text">{description}</p>
   <Checkbox checked={confirmed} disabled={blocked} aria-describedby={`${id}-description`} onChange={event=>setConfirmed(event.target.checked)}>{confirmationLabel}</Checkbox>
   <div className="action-row"><Button variant="secondary" disabled={blocked} onClick={cancel}>Vazgeç</Button><Button variant={variant} loading={pending||busy} disabled={disabled||!confirmed} onClick={()=>void confirm()}>{label} — onayla</Button></div>
   {error&&<Alert tone="error" role="alert">{error}</Alert>}
  </div>}
 </div>;
}
