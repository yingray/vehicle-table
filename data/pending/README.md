# data/pending — 尚未併入的資料

這裡的檔案**還沒進 `data/vehicles.json`**，因為它們少了最後一道品管。

## german-batch3.json

Mercedes-Benz / BMW / Audi 共 50 筆。已完成「研究 → 對抗式查核」兩道，
但**跨車款交叉檢查與修補階段被中斷**（2026-08-12），所以可能還帶著
單一品牌內部互相矛盾的數字（例如大型 SUV 保養費比小型房車還低）。

要併入前先跑完那一步，不要直接倒進 `data/vehicles.json`。

## 併入後

確認無誤就把這個目錄整個刪掉，資料的唯一來源是 `data/vehicles.json`。
