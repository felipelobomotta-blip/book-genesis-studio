const {test}=require('node:test');
const assert=require('node:assert/strict');
const {createStudioRefresh}=require('../../runner/web/studio_poll.js');

test('post-action refresh waits for stale response then loads fresh state',async()=>{
  let calls=0, release;
  const refresh=createStudioRefresh(async()=>{calls++;if(calls===1)await new Promise(resolve=>release=resolve);return calls;});
  const poll=refresh();await Promise.resolve();
  const afterAction=refresh(true);
  assert.equal(calls,1);release();
  assert.equal(await poll,1);assert.equal(await afterAction,2);assert.equal(calls,2);
});
test('ordinary overlapping polls share a request',async()=>{
  let calls=0;const refresh=createStudioRefresh(async()=>++calls);
  await Promise.all([refresh(),refresh(),refresh()]);assert.equal(calls,1);
});
test('failed request does not permanently block refresh',async()=>{
  let calls=0;const refresh=createStudioRefresh(async()=>{if(++calls===1)throw Error('offline');return 'online';});
  await assert.rejects(refresh());assert.equal(await refresh(),'online');
});
