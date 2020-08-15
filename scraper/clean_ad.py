# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 23:59:03 2020

@author: iima
"""

import pandas as pd
import re
import numpy as np

data = pd.read_csv('F:\\Github\\esun_competition\\content_df_0612.csv')

def search_context(context_s, rc, a):
    min_len = min(len(context_s[0]), len(context_s[1]))
    if a > (min_len+5):
        return ''
    else:
        temp = len(context_s[0])
        pat1 = context_s[0][(temp-5-a):(temp-a)]
        pat2 = context_s[1][a:(5+a)]
        # 前後5個字做正則匹配，DOTALL可匹配\n
        pattern = re.compile(f'{pat1}(.*){pat2}', re.DOTALL)
        extract = re.search(pattern, rc)
        try:
            content = extract.group(1)
        except:
            a += 1
            content = search_context(context_s, rc, a)
        
        return context_s[0] + content[a:(len(content)-a)] + context_s[1]
    

# 清理前後文
def extract_content(context: pd.Series, raw_content: pd.Series) -> pd.Series:
    a = 0
    temp_list = []
    results = []
    # ct = data.iloc[159, 2]
    # rc = data.iloc[159, 4]
    for ct, rc in zip(context, raw_content):
        print(a)
        if rc is np.nan:
            temp_list.append('')
            results.append(('no raw', -1, -1))
        else:
            # 清符號(為了正則匹配)，以"省略內文"分前後文
            context_s = re.sub('[*.?(){}\[\]\\\\+]', '', ct).split(' ### 省略內文 ### ')
            # 主辦有一些是上下文一膜一樣重複兩次的，直接跳過不處理
            if context_s[0] == context_s[1]: 
                content = rc
                result = ('double', -1, -1)
            else:
                up_context = re.sub('<BR>', '', context_s[0]) # 上文
                down_context = re.sub('<BR>.*', '', context_s[1]) # 下文； BR後面很多是廣告，直接刪掉

                # window = 5個字，往前滑動尋找匹配的到的上文
                min_up = [len(rc), -1] # [開始位置，i] 兩兩比較排序，為了找最大長度
                # 防止字數太少，range(0, 0)迴圈會不跑
                if len(up_context) == 0:
                    temp = 0
                elif len(up_context)-5 <= 1:
                    temp = 1
                else:
                    temp = len(up_context)-5
                    
                for i in range(0, temp):
                    all_index = re.finditer(up_context[(len(up_context)-5-i):(len(up_context)-i)], rc)
                    start_index = [ai.start() for ai in all_index]
                    if start_index == []:
                        start_index = -1
                    else:
                        start_index = start_index[0]
                    if start_index != -1:
                        if start_index < min_up[0]: # 新找到的start_index比舊的前面
                            min_up[0] = start_index
                            min_up[1] = i
                if min_up[1] == -1: # 如果都沒找到，從最前面開始取
                    min_up = [0, -1]
 
                # window = 5個字，往後滑動尋找匹配的到的下文
                min_down = [0, -1] # [開始位置，j] 兩兩比較排序
                # 防止字數太少，range(0, 0)迴圈會不跑
                if len(down_context) == 0:
                    temp = 0
                elif len(down_context)-5 <= 1:
                    temp = 1
                else:
                    temp = len(down_context)-5
                for j in range(0, temp):
                    all_index = re.finditer(down_context[j:(5+j)], rc)
                    end_index = [ei.start() for ei in all_index]
                    if end_index == []:
                        end_index = -1
                    else:
                        end_index = end_index[-1]
                        
                    if end_index != -1:
                        if end_index > min_down[0]: # 新找到的end_index比已記錄的後面
                            min_down[0] = end_index
                            min_down[1] = j
                if min_down[1] == -1: # 如果都沒匹配到，取到最後面
                    min_down = [len(rc), -1]

                        
                # 前面改了不想改後面，所以改命名
                start_index, i = min_up
                end_index, j = min_down
                # 上文發現點 比 下文發現點 早
                if start_index <= end_index:
                    if (i != -1) & (j != -1): # 找到上文 & 找到下文
                        # 把匹配到的字數，從content裡面去掉
                        # 比如 前文往前推i個字，前文就剩下[(結尾-i-5):(結尾-i)]； 後文則是往後j個字，就剩下[(0+j):(0+j+5)]
                        # 則內文的"上文匹配位置"要往後5個字，"下文匹配位置"不需要調整。(匹配index與i, j無關，找到哪裡就是哪裡開始)
                        content = up_context[:(len(up_context)-i)] + rc[(start_index+5):(end_index)] + down_context[j:]
                        result = ('success', start_index, end_index)
                    elif (i == -1) & (j != -1): # 沒找到上文
                        content = rc[:(end_index-j)] + down_context[j:]
                        result = ('no up', -1, end_index)
                    elif (i != -1) & (j == -1): # 沒找到下文
                        content = up_context[:-i] + rc[(start_index+i):]
                        result = ('no down', start_index, -1)
                    else: # 上下文都沒找到
                        content = rc
                        result = ('error', -1, -1)
                else:
                    content = rc
                
                # 不管怎麼做都會有例外，一部分是因為raw_content不一定抓的跟主辦一樣
                # 一部份是主辦的資料也可能有錯，直接從字數下手
                # 字數<100都直接用raw
                if len(content) < 100:
                    content = rc
                    result = ('too less', -1, -1)
                if len(content) < 100:
                    content = up_context + rc + down_context
                    result = ('too less2', -1, -1)
                
            temp_list.append(content)
            results.append(result)
        a += 1
    return pd.Series(temp_list), results

pds_content, results = extract_content(data['context'], data['raw_content'])
data['content'] = pds_content

# 執行結果
pd.Series([ss[0] for ss in results]).value_counts()
# 內文不加上下文
clean_contetnt = pd.Series([ss[2]-ss[1] for ss in results])
# 看起來除了沒爬到的都找到了，有點可怕，所以我另外再檢查一次
# 正常的結果，應該是1. raw必然>=content 2. content>context，而且字不會太少
diff = data['raw_content'].str.len() - clean_contetnt
diff1 = data['content'].str.len() - data['context'].str.len()
data['raw_diff'] = diff
data['context_diff'] = diff1
data['content_status'] = pd.Series([ss[0] for ss in results])

temp = data.loc[(~data['raw_content'].isna()) & ((data['raw_diff']<=0) | (data['context_diff']<=20))]
# double 基本沒問題
temp = temp.loc[temp['content_status'] != 'double']
# error 


target = 4410
data.iloc[target, 0] # id
data.iloc[target, 1] # url
data.iloc[target, 2] # context
data.iloc[target, 4] # raw
data.iloc[target, 6] # content
results[target] # 不加context的樣子
data.iloc[target, 4][results[target][1]:results[target][2]]

# 3547，主辦抓到下面廣告
# 3639，主辦把"1."去掉
# 2194，主辦的前後文是 兩次重複的全文
# 2252，url多一個空白
# 1712, 4375, 4750，hk01全部放棄，都是動態網頁，還有換頁
# 爬蟲再修改一下，可以多抓到10篇以內的文章，其中有一篇是AML
# 4037，實際上沒有省略的內文
# 2730，主辦的下文，根本不在原文裡

# BR後面是廣告部分484通例
temp1 = data.loc[data['context'].str.match('.*<BR>.*')]
temp2 = temp1['context'].str.split('省略內文')
temp2 = temp2.apply(lambda x: x[1])
temp2 = temp2.str.extract('(<BR>.*)')
# 基本都是沒用的東西

# save
data1 = data.drop(columns=['raw_diff', 'context_diff'])
data1.to_csv('F:\\Github\\esun_competition\\content_df_0620.csv', index=False)

(data['raw_content'].str.len().mean() - data['content'].str.len().mean())/data['raw_content'].str.len().mean()

data2 = pd.read_csv('F:\\Github\\esun_competition\\content_df_0620.csv')
data1['str_len'] = data1['content'].str.len()
