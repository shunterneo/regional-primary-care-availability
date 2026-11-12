const fs=require('fs'),vm=require('vm'),assert=require('assert');
const ctx={C:[],Date};vm.createContext(ctx);vm.runInContext(fs.readFileSync('scripts/freshness.js','utf8'),ctx);
const rows=[{display_status:'accepting',display_expires_on:'2026-11-23'},{display_status:'not_accepting',display_expires_on:'2026-11-23'},{display_status:'unknown'}];
assert.equal(ctx.expireEvidence(rows,new Date('2026-11-22T23:59:59Z')),false);
assert.equal(ctx.expireEvidence(rows,new Date('2026-11-23T00:00:00Z')),true);
assert.equal(rows[0].display_status,'needs_review');assert.equal(rows[1].display_status,'needs_review');assert.equal(rows[2].display_status,'unknown');
assert.equal(ctx.expireEvidence(rows,new Date('2026-11-24')),false);
console.log('PASS: browser expiry for positive/negative evidence, no upgrades, repeat-safe');
