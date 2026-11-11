// Execute the deployed site's actual JavaScript with a minimal DOM. No browser/network dependency.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/../site/index.html','utf8');
const dataMatch=html.match(/<script id="clinic-data" type="application\/json">([\s\S]*?)<\/script>/);
const scriptMatch=html.match(/<script>\s*('use strict';[\s\S]*?)<\/script>/);
assert(dataMatch&&scriptMatch,'embedded data and UI script');
const DATA=JSON.parse(dataMatch[1]);const N=DATA.clinics.length;const numFor=(k)=>DATA.clinics.filter(x=>['ongoing','both'].includes(x.care_model)&&x.display_status===k).length;const TOWNS=new Set(DATA.clinics.map(x=>x.community)).size;const countTown=t=>DATA.clinics.filter(x=>x.community===t&&['ongoing','both'].includes(x.care_model)).length;const countModel=k=>DATA.clinics.filter(x=>x.care_model===k).length;const countOngoing=()=>DATA.clinics.filter(x=>['ongoing','both'].includes(x.care_model)).length;
class Node{
 constructor(tag='',cls='',text=''){this.tag=tag;this.className=cls;this.textContent=text;this.children=[];this.handlers={};this.value='all';this.href='';this.style={};this.attrs={};}
 append(x){this.children.push(x);return x}replaceChildren(...nodes){this.children=[...nodes]}
 setAttribute(k,v){this.attrs[k]=v}addEventListener(k,callback){this.handlers[k]=callback}
 scrollIntoView(){}get innerText(){return this.textContent+' '+this.children.map(x=>x.innerText).join(' ')}
 get count(){return this.children.length}
}
const ids={};for(const id of ['clinic-data','last','mTotal','mIntake','mLeads','mReview','town','status','care','search','reset','map','count','results','find','footerstatus','changeHistory'])ids[id]=new Node(id);
ids['clinic-data'].textContent=dataMatch[1];
const document={getElementById(id){assert(ids[id],`missing id: ${id}`);return ids[id]},createElement(tag){return new Node(tag)},createElementNS(ns,tag){return new Node(tag)}};
vm.runInNewContext(scriptMatch[1],{document,console,Math,Set,JSON,Intl}, {timeout:3000,filename:'site-inline.js'});
assert.equal(ids.mTotal.textContent,N);assert.equal(ids.mIntake.textContent,numFor('accepting'));assert.equal(ids.mLeads.textContent,numFor('reported'));
assert.equal(ids.results.children.length,countOngoing());assert.equal(ids.map.children.filter(x=>x.tag==='g').length,TOWNS);
ids.status.handlers.change({target:{value:'accepting'}});assert.equal(ids.results.children.length,numFor('accepting'));
ids.status.handlers.change({target:{value:'reported'}});assert.equal(ids.results.children.length,numFor('reported'));
ids.status.handlers.change({target:{value:'all'}});
ids.care.handlers.change({target:{value:'both'}});assert.equal(ids.results.children.length,countModel('both'));
ids.care.handlers.change({target:{value:'walkin'}});assert.equal(ids.results.children.length,countModel('both')+countModel('walk_in_only'));
ids.care.handlers.change({target:{value:'walk_in_only'}});assert.equal(ids.results.children.filter(n=>n.className==='item').length,countModel('walk_in_only'));assert(!ids.map.children.some(n=>n.tag==='g') || countModel('walk_in_only')>0);
ids.care.handlers.change({target:{value:'ongoing'}});
ids.search.handlers.input({target:{value:'Oxfordia'}});const match=C=>C.filter(c=>c.name.toLowerCase().includes('oxfordia')).length;assert.equal(ids.results.children.length,match(DATA.clinics));
ids.reset.handlers.click();assert.equal(ids.results.children.length,countOngoing());
ids.town.handlers.change({target:{value:'Tillsonburg'}});assert.equal(ids.results.children.length,countTown('Tillsonburg'));
assert(!/home.address|residential address geocod|Google Map/i.test(ids.last.innerText));
console.log(`PASS: ${N} records; ${numFor("accepting")} direct; ${numFor("reported")} reported; clinic filters and ${TOWNS} SVG markers; no patient-address entry`);
