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
const document={handlers:{},addEventListener(k,callback){this.handlers[k]=callback},getElementById(id){assert(ids[id],`missing id: ${id}`);return ids[id]},createElement(tag){return new Node(tag)},createElementNS(ns,tag){return new Node(tag)}};
const timers=[];const context={document,console,Math,Set,JSON,Intl,TextEncoder,setInterval(fn){timers.push(fn)}};
vm.runInNewContext(scriptMatch[1].replace('})();','globalThis.features={setFilter,chosen,filterControls,openEditor,reviewEdit,pdfBytes,docxBytes,csvBytes,exportRows,selectedClinics};})();'),context, {timeout:3000,filename:'site-inline.js'});
assert.equal(ids.mTotal.textContent,N);assert.equal(ids.mIntake.textContent,numFor('accepting'));assert.equal(ids.mLeads.textContent,numFor('reported'));
assert.equal(ids.results.children.length,countOngoing());assert.equal(ids.map.children.filter(x=>x.tag==='g').length,TOWNS);
context.features.setFilter('status',['accepting']);assert.equal(ids.results.children.length,numFor('accepting'));
context.features.setFilter('status',['reported']);assert.equal(ids.results.children.length,numFor('reported'));
context.features.setFilter('status',['all']);
context.features.setFilter('care',['both']);assert.equal(ids.results.children.length,countModel('both'));
context.features.setFilter('care',['walkin']);assert.equal(ids.results.children.length,countModel('both')+countModel('walk_in_only'));
context.features.setFilter('care',['walk_in_only']);assert.equal(ids.results.children.filter(n=>n.className==='item').length,countModel('walk_in_only'));assert(!ids.map.children.some(n=>n.tag==='g') || countModel('walk_in_only')>0);
context.features.setFilter('care',['ongoing']);
ids.search.handlers.input({target:{value:'Oxfordia'}});const match=C=>C.filter(c=>c.name.toLowerCase().includes('oxfordia')).length;assert.equal(ids.results.children.length,match(DATA.clinics));
ids.reset.handlers.click();assert.equal(ids.results.children.length,countOngoing());
context.features.setFilter('town',['Tillsonburg']);assert.equal(ids.results.children.length,countTown('Tillsonburg'));
assert(!/home.address|residential address geocod|Google Map/i.test(ids.last.innerText));
ids.reset.handlers.click();ids.mapMode.handlers.change({target:{value:'clinics'}});assert(ids.mapDetail.textContent.includes('sourced clinic points'));assert(ids.map.children.some(n=>n.tag==='g'));context.features.setFilter('town',['Tillsonburg']);assert(ids.mapDetail.textContent.includes('filtered listings'));ids.mapMode.handlers.change({target:{value:'towns'}});ids.reset.handlers.click();
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

// A continuously visible tab must downgrade without reload or focus changes.
const expired=f.exportRows().find(c=>c.display_status==='accepting');assert(expired);
expired.display_expires_on='2000-01-01';timers[0]();
assert.equal(expired.display_status,'needs_review');
assert.equal(ids.mIntake.textContent,numFor('accepting')-1);
assert(f.csvBytes([expired]).includes('Needs reconfirmation'));
assert(f.pdfBytes([expired]).includes('Needs reconfirmation'));
assert(new TextDecoder().decode(f.docxBytes([expired])).includes('Needs reconfirmation'));
// Direct export functions defend against expiry between selection and saving.
for(const encode of [f.csvBytes,f.pdfBytes,f.docxBytes]){
 const stale={...expired,display_status:'accepting'};encode([stale]);assert.equal(stale.display_status,'needs_review');
}
console.log('PASS: visible-tab timer and actual CSV/PDF/DOCX expiry guards');

// Exporting before the timer must also refresh visible cards/map, not swallow the change.
ids.reset.handlers.click();ids.downloadScope.value='all';
const raced=f.exportRows().find(c=>c.display_status==='accepting');assert(raced);
raced.display_expires_on='2000-01-01';f.exportRows();timers[0]();
const racedCard=ids.results.children.find(card=>card.innerText.includes(raced.name));
assert(racedCard&&racedCard.innerText.includes('Needs reconfirmation'));
assert(!racedCard.children.find(n=>n.className==='pills').children.some(n=>n.className==='pill accepting'));
console.log('PASS: export-first expiry also refreshes visible cards before timer');

// Detail-only corrections and new additions must render without false status claims.
assert(html.includes('Recent directory updates'));
assert(!ids.changeHistory.innerText.includes('null →'));
for (const entry of DATA.change_history.slice(0,10)) {
 if(entry.summary) assert(ids.changeHistory.innerText.includes(entry.summary),'Missing scoped change summary');
}
console.log('PASS: recent corrections render summaries without null statuses');

// Multiselect: OR within a field, AND across fields; actual checkbox change handlers.
ids.reset.handlers.click();
const ctl=f.filterControls;
function tick(id,value,checked){const input=ctl[id].inputs.find(x=>x[0]===value)[1];input.checked=checked;input.handlers.change()}
tick('status','reported',true);tick('status','waitlist',true);
const expected=DATA.clinics.filter(c=>['ongoing','both'].includes(c.care_model)&&['reported','waitlist'].includes(c.display_status));
assert.equal(ids.results.children.filter(x=>x.className==='item').length,expected.length);
assert(ids.statusSummary.textContent.includes('Waitlist'));
const twoTowns=[...new Set(expected.map(c=>c.community))].slice(0,2);
for(const t of twoTowns)tick('town',t,true);
assert.equal(ids.results.children.filter(x=>x.className==='item').length,expected.filter(c=>twoTowns.includes(c.community)).length);
ids.downloadScope.value='filtered';assert.equal(f.exportRows().length,expected.filter(c=>twoTowns.includes(c.community)).length);
ids.statusAll.handlers.click();assert.equal(f.chosen.status.length,0);
ids.townAll.handlers.click();tick('care','unverified',true);
assert.equal(f.exportRows().length,DATA.clinics.filter(c=>['ongoing','both','unverified'].includes(c.care_model)).length);
ids.careAll.handlers.click();assert.equal(f.exportRows().length,N);
ids.status.open=true;ids.status.handlers.keydown({key:'Escape'});assert.equal(ids.status.open,false);
ids.reset.handlers.click();assert.deepEqual(Array.from(f.chosen.care),['ongoing']);assert.equal(f.chosen.status.length,0);assert.equal(f.chosen.town.length,0);
assert.equal(f.exportRows().length,countOngoing());
console.log('PASS: multiple statuses/communities/care types, OR/AND combinations, filtered export, Show all, reset, Escape');
