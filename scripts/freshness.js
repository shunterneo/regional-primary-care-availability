// Downgrade expired evidence even if the static host has not rebuilt. Never upgrade.
function expireEvidence(rows, now=new Date()) {
 const today=now.toISOString().slice(0,10);let changed=false;
 for(const c of rows)if(c.display_expires_on&&today>=c.display_expires_on&&!['unknown','needs_review'].includes(c.display_status)){
  c.display_status='needs_review';changed=true;
 }
 return changed;
}
expireEvidence(C);
