# Course Grabber

## Usage

Wirte a open main.py in root folder

```python
from modules.school import NTUST

if __name__ == '__main__':
    me = NTUST() # 實例化
    me.login({'studentno': '你的學號', 'idcard': '你的身分證後四碼',
              'DropMonth': '你的生月', 'DropDay': '你的生日', 'password': '你的密碼'})
    me.grab('課程代碼')
```

## Guide

grab
> 持續加選

choose
> 加選一次

## ToDo

* [ ] 優化線程 可以及時加入、終止
* [ ] 新增圖形介面
* [ ] 新增 CLI
* [ ] 將登入資訊改為讀取 `json` 檔
