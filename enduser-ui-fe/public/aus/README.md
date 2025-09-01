 前置準備 (Prerequisites)

  在開始之前，請先確認您的電腦已經安裝好以下軟體：

   1. VS Code: 程式碼編輯器。 下載連結 (https://code.visualstudio.com/download)
   2. Git: 版本控制工具。 下載連結 (https://git-scm.com/downloads)
   3. GitHub 帳號: 您需要一個 GitHub 帳號來存放您的專案。 註冊連結 (https://github.com/signup)

  ---

  完整流程：從本機端到雲端 GitHub

  這個流程會帶您從建立一個本地資料夾開始，將它變成一個 Git 儲存庫 (Repository)，最後再推送到
  GitHub。

  步驟一：在本機建立專案資料夾與 Git 儲存庫

  首先，我們需要建立一個專案資料夾，並在裡面初始化 Git 儲存庫。

   1. 開啟終端機 (Terminal)
       * 在 VS Code 中，您可以透過 Ctrl + ` ` (反引號鍵) 來開啟內建的終端機。

   2. 建立專案資料夾並進入
       * 在終端機中，輸入以下指令來建立一個名為 my-git-project 的資料夾，並進入該資料夾。

   1     mkdir my-git-project
   2     cd my-git-project

   3. 用 VS Code 開啟此資料夾
       * 這個指令會讓 VS Code 的工作區直接鎖定在這個資料夾，方便後續操作。

   1     code .

   4. 初始化 Git 儲存庫
       * 在 my-git-project 資料夾中，執行以下指令來初始化 Git 儲存庫。

   1     git init
       * 您會看到一個回應 Initialized empty Git repository in
         C:/Users/Vincent/my-git-project/.git/，這表示 Git 儲存庫已經成功建立。

   5. 設定您的 Git 使用者名稱與 Email
       * 這是非常重要的一步，因為這會讓 GitHub 知道是誰上傳了這些程式碼。請將
         info.vincent.kwok@gmail.com 換成您的 Email。

   1     git config user.name "Vincent"
   2     git config user.email "info.vincent.kwok@gmail.com"

 步驟二：建立檔案並提交到本地儲存庫

  現在我們來建立一個檔案，並將它提交 (Commit) 到本地的 Git 儲存庫。

   1. 建立一個檔案
       * 您可以在 VS Code 的檔案總管中手動建立，或是在終端機中執行以下指令來建立一個 README.md 檔案。

   1     echo "# My Awesome Project" >> README.md

   2. 檢查儲存庫狀態
       * 執行 git status 來查看目前儲存庫的狀態。您會看到 README.md 是一個 "Untracked file"。

   1     git status

   3. 將檔案加入暫存區 (Staging Area)
       * 使用 git add 指令來將檔案加入暫存區。

   1     git add .
       * . 代表加入所有變更的檔案。您也可以指定特定檔案，例如 git add README.md。

   4. 提交變更
       * 使用 git commit 指令來將暫存區的檔案提交到儲存庫。

   1     git commit -m "Initial commit"
       * -m 後面接著的是這次提交的訊息，請務必填寫有意義的訊息。

  步驟三：在 GitHub 上建立遠端儲存庫

  接下來，我們要在 GitHub 上建立一個空的儲存庫，用來存放我們本地的程式碼。

   1. 登入 GitHub
       * 前往 github.com (https://github.com) 並登入。

   2. 建立新儲存庫
       * 點擊右上角的 + 圖示，然後選擇 New repository。
       * Repository name: 輸入 my-git-project (建議與本地資料夾同名)。
       * Description: 簡單描述您的專案 (選填)。
       * Public / Private: 選擇您要公開還是私有。
       * Initialize this repository with: 不要勾選任何選項 (Add a README file, Add .gitignore, Choose
          a license)。因為我們已經有本地的儲存庫了。
       * 點擊 Create repository。

  步驟四：將本地儲存庫與 GitHub 儲存庫連結

  現在，我們要把本地的儲存庫與剛剛在 GitHub 上建立的遠端儲存庫連結起來。

   1. 複製遠端儲存庫的 URL
       * 在 GitHub 儲存庫頁面上，您會看到 "…or push an existing repository from the command line"
         的區塊。請複製底下的
         URL，它看起來會像這樣：https://github.com/your-username/my-git-project.git。

   2. 將遠端儲存庫加入本地設定
       * 回到您的終端機，執行以下指令。請記得將 URL 換成您自己的。

   1     git remote add origin https://github.com/your-username/my-git-project.git
       * origin 是遠端儲存庫的預設名稱。

   3. 將本地分支重新命名為 main (建議)
       * GitHub 的預設分支名稱是 main，我們可以透過以下指令將本地分支也改為 main。

   1     git branch -M main

   4. 將本地程式碼推送到 GitHub
       * 最後，使用 git push 指令將您的程式碼推送到 GitHub。

   1     git push -u origin main
       * -u 參數會設定本地的 main 分支去追蹤遠端的 main 分支。未來您只需要輸入 git push 即可。

  步驟五：驗證與後續開發

   1. 重新整理 GitHub 頁面
       * 回到您的 GitHub 儲存庫頁面並重新整理，您應該會看到您剛剛提交的 README.md 檔案。

   2. 日常開發流程
       * 現在您的本地儲存庫已經與 GitHub 連結。之後的開發流程會是：
           1. 在 VS Code 中修改或新增檔案。
           2. 使用 git add . 將變更加入暫存區。
           3. 使用 git commit -m "Your commit message" 提交變更。
           4. 使用 git push 將變更推送到 GitHub。

  總結

  這就是一個完整的 ls (本機) -> git -> GitHub (雲端) 的流程。

   * `ls`: 確認您的檔案。
   * `git add`: 將變更加入暫存區。
   * `git commit`: 將暫存區的變更提交到本地儲存庫。
   * `git push`: 將本地儲存庫的變更推送到遠端 GitHub 儲存庫。
