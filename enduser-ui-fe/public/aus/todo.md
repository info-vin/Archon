# study
- 你是一位全端網站的設計師. 解釋用繁體中文說明 設計步驟與內容
- 理解 @\151_require\v1.1.md\ 內 "文件清單與週計畫", 將周計畫工作內容配合所需要的文件名稱以清單方式列表.
- 說明列表對應關係,如第一周計畫需提供那些幾份文件.這樣你的主管可以知道每一周完成那些文件與進度. 

# create folder
- [ ] 新增kanban-demo檔案夾,存放所有網站設計程式
- [ ] 參考"kanban"設計 現代化網站web application, 可以參考其他UI/UX設計網站.讓其他同事可以同步配合.
- [ ] 使用 ts 生成前端與後端的程式碼,
       可以前後端分離啟動,
       例如：Kanban 看板的 HTML 結構、任務卡片的 CSS 樣式、拖放功能的 JavaScript 邏輯,
       將@\151_require\V1.1.1.md項目資料分別填入卡片,
       可以記錄編輯與移動卡片,讓網站可以實際使用.
       加入左方功能導覽列.       


# update this file


# 153_testCase prompt
你是一位系統專案分析師,完成以下事項:
1.理解 @\153_testCase\Fujitec_Intelligent_Scheduling_Project.html 文件內說明事項包含程式碼.
2.a 解讀業務的信件內容 @\153_testCase\reply_email.md
2.b 客戶的痛點挑戰 @\153_testCase\sas_viya_features_table.md
3. 結合以上3份文件內容, 挑選poc的驗證指標,需要配合前面html文件內容有詳細實際範例補充說明.
4. 新增"建議回覆"內容於 @\153_testCase\Fujitec_Intelligent_Scheduling_Project.html ,整合於"手冊導覽"最後項目,注意符合中英文翻譯.修改完成後的html檔案另存於 @\153_testCase\dis_v0.1.1.html
5. 先說明你的工作步驟後,讓業務主管決定你可以繼續修改html檔.
6. 測試文件按鈕,尤其是中英文切換能否正常運作,測試報告用log的方式記錄在 @\153_testCase\log.txt.

# issue the \" in javascript


Hi [Name],
Thank you for your question regarding IPA/RPA integration in PoC scope.
Regarding IPA/RPA Implementation Strategy:
You're correct that IPA/RPA is not included in the initial PoC phase, and here's our rationale:
Technical Validation Limitations:

For this PoC, we can only validate REST API transmission results (similar to Postman testing)
The effectiveness heavily depends on the quality and validity of customer-provided data
If RPA is deployed on-premises, all data and models remain within the company's internal systems, 
making it impossible for external personnel to diagnose system errors or anomalies.
To avoid potential disputes and ensure clear accountability, 
we plan to complete single-system testing before proceeding to integration testing


### "Brain and Hands" Model - Future Integration:
As outlined in Chapter 11 of proposal, we do envision the IPA/RPA integration following the "Brain and Hands" model:

> The Brain (SAS Viya): Handles complex analytics and decision-making for optimal scheduling
>
> The Hands (RPA Bot): Executes repetitive tasks, such as automatically populating Excel reports based on SAS Viya's output

### SAS Viya Native Workflow Capabilities:
As mentioned in last month's Hsinchu facility meeting, the SAS Viya Flow Management Interface (as shown in the attached screenshot) already provides comprehensive [workflow management](https://docs.google.com/presentation/d/1bZQfa4BtP3MT6kr3Wf3gHp7iMB4X6MN94nI18b3ddYw/edit?slide=id.g3602673f385_0_296#slide=id.g3602673f385_0_296) capabilities:

#### Process management with visual operation status monitoring
* Automated deployment
* Graphical workflow design and image-based operations
* Custom evaluation metrics
* Exception alerting

### Recommendation:
Unless the customer specifically prioritizes understanding the File I/O dependencies between IPA and RPA integration, we suggest focusing the initial PoC on:

* Core SAS Viya analytics and scheduling capabilities
* Data integration and validation
* Workflow management using SAS Viya's native interface

This approach ensures a solid foundation before adding the complexity of RPA integration.

你是一位全端網站的設計師 @GEMINI.md @網頁專案轉型登陸頁面_.md,
深入思考如何設計index.tsx:
1. 保留全網站都能多語系, 例如: 英文, 中文, 日文, 韓文, 越南文等.
2. 網站設計要能夠新增使用者, 例如: 註冊, 登入, 忘記密碼等.
3. 網站設計要符合台灣的法律規定, 例如: 隱私權保護, 安全保護等.
4. 網站設計要多增加哪些免費的小型資料庫. 
5. 網站設計可以直接上傳網頁檔案, 例如: 上傳csv檔案, 上傳pdf檔案等.
6. 考慮同樣的架構下增加"ai"是一種產品,"AUS"是另一種產品.
等主管確認完你的設計說明後:
1. 將說明更新至@GEMINI.md 再commit dev分支.
2. 新增branch feature分支,切換feature在開始修改程式,並將測試結果更新至@GEMINI.md.

你是一位全端網站的設計師 @GEMINI.md