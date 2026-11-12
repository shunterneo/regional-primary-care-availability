// Execute the deployed site's actual JavaScript with a minimal DOM. No browser/network dependency.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/../site/index.html','utf8');
const dataMatch=html.match(/<script id="clinic-data" type="application\/json">([\s\S]*?)<\/script>/);
const scriptMatch=html.match(/<script>\s*('use strict';[\s\S]*?)<\/script>/);
assert(dataMatch&&scriptMatch,'embedded data and UI script');
const DATA=JSON.parse(dataMatch[1]);const N=DATA.clinics.length;const numFor=(k)=>DATA.clinics.filter(x=>['ongoing','both'].includes(x.care_model)&&x.display_status===k).length;const TOWNS=new Set(DATA.clinics.map(x=>x.community)).size;const countTown=t=>DATA.clinics.filter(x=>x.community===t&&['ongoing','both'].includes(x.care_model)).length;const countModel=k=>DATA.clinics.filter(x=>x.care_model===k).length;const countOngoing=()=>DATA.clinics.filter(x=>['ongoing','both'].includes(x.care_model)).length;
class Node{
 constructor(tag='',cls='',text=''){this.tag=tag;this.className=cls;this.textContent=text;this.children=[];this.handlers={};this.value='all';this.href='';this.style={};this.attrs={};}
 prepend(x){this.children.unshift(x);return x}append(x){this.children.push(x);return x}showModal(){this.open=true}close(){this.open=false}remove(){}focus(){}select(){}click(){if(this.handlers.click)this.handlers.click()}set id(v){this._id=v;ids[v]=this}get id(){return this._id}replaceChildren(...nodes){this.children=[...nodes]}
 setAttribute(k,v){this.attrs[k]=v}addEventListener(k,callback){this.handlers[k]=callback}
 scrollIntoView(){}get innerText(){return this.textContent+' '+this.children.map(x=>x.innerText).join(' ')}
 get count(){return this.children.length}
}
const ids={};for(const m of html.matchAll(/\bid="([^"]+)"/g))ids[m[1]]=new Node(m[1]);
ids['clinic-data'].textContent=dataMatch[1];
const document={getElementById(id){assert(ids[id],`missing id: ${id}`);return ids[id]},createElement(tag){return new Node(tag)},createElementNS(ns,tag){return new Node(tag)}};
const context={document,console,Math,Set,JSON,Intl,TextEncoder};
vm.runInNewContext(scriptMatch[1].replace('})();','globalThis.features={openEditor,reviewEdit,pdfBytes,docxBytes,csvBytes,exportRows,selectedClinics};})();'),context, {timeout:3000,filename:'site-inline.js'});
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
ids.reset.handlers.click();ids.mapMode.handlers.change({target:{value:'clinics'}});assert(ids.mapDetail.textContent.includes('sourced clinic points'));assert(ids.map.children.some(n=>n.tag==='g'));ids.town.handlers.change({target:{value:'Tillsonburg'}});assert(ids.mapDetail.textContent.includes('filtered listings'));ids.mapMode.handlers.change({target:{value:'towns'}});ids.reset.handlers.click();
console.log(`PASS: ${N} records; ${numFor("accepting")} direct; ${numFor("reported")} reported; clinic filters and ${TOWNS} SVG markers; no patient-address entry`);

// Exercise the actual export and editor code, with a one-clinic selected subset.
const f=context.features;f.selectedClinics.add('c011');ids.downloadScope.value='selected';assert.equal(f.exportRows().length,1);assert.equal(f.exportRows()[0].id,'c011');
ids.downloadScope.value='all';assert.equal(f.exportRows().length,N);
const ox=DATA.clinics.find(c=>c.id==='c011');f.openEditor(ox);assert(ids.editDialog.open);ids['edit-phone'].value='519-555-0101';ids.editNote.value='Fixture source reviewed for phone correction.';f.reviewEdit();assert(!ids.editReview.hidden);assert(ids.editApprove.disabled);ids.editConfirm.value='wrong';ids.editAcknowledged.checked=true;ids.editConfirm.handlers.input();assert(ids.editApprove.disabled);ids.editConfirm.value='c011';ids.editConfirm.handlers.input();assert(!ids.editApprove.disabled);ids.editApprove.handlers.click();assert(!ids.editPublishSteps.hidden);assert.equal(JSON.parse(ids.editCode.value).changes.phone,'519-555-0101');assert.equal(ox.phone,'519-926-6752');
assert(f.csvBytes([{name:'=DANGEROUS',display_status:'unknown'}]).includes("'=DANGEROUS"));
if(process.env.EXPORT_FIXTURE_DIR){fs.mkdirSync(process.env.EXPORT_FIXTURE_DIR,{recursive:true});fs.writeFileSync(process.env.EXPORT_FIXTURE_DIR+'/selected.pdf',f.pdfBytes([ox]));fs.writeFileSync(process.env.EXPORT_FIXTURE_DIR+'/selected.docx',f.docxBytes([ox]));fs.writeFileSync(process.env.EXPORT_FIXTURE_DIR+'/all.pdf',f.pdfBytes(DATA.clinics));}
console.log('PASS: selected/all exports, CSV injection protection, edit review and typed confirmation; live data unchanged');
const researched=DATA.clinics.find(c=>c.online_review_text);
assert(researched,'research finding present');
assert(ids.results.children.some(card=>card.children.some(n=>n.className==='research')),'research disclosure rendered');
assert(f.csvBytes([researched]).includes(researched.online_review.finding.replace(/"/g,'""')),'CSV preserves research finding');
assert(f.pdfBytes([researched]).includes('Online research:'),'PDF preserves research context');
assert(new TextDecoder().decode(f.docxBytes([researched])).includes('Online research:'),'Word preserves research context');
console.log('PASS: research disclosures and CSV/PDF/Word research provenance');
