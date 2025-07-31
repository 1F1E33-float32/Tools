'use strict';
require('frida-il2cpp-bridge');

rpc.exports = {
  hash(samples) {
    Il2Cpp.perform(() => {
      const asm       = Il2Cpp.domain.assembly("Assembly-CSharp");
      const image     = asm.image;
      const AmberHash = image.class("Amber.Hash");
      const getHash   = AmberHash.method("GetHashCode");

      for (const s of samples) {
        const h = getHash.invoke(Il2Cpp.string(s), 0);
        send(`${s},${h}`);
      }
      send('done');
    });
  }
};