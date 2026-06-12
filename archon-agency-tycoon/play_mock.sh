#!/bin/bash

# Archon: Agency Tycoon - Terminal Prototype
# 這是一個極簡的 MVP，用來驗證遊戲的 TDD 核心邏輯 (狀態機與時間流逝)

FUNDS=500
REP=100
TICK=1
MSG=""

# --- 資料庫 (Data Model) ---
# Agent
A_NAME=("Alice" "Bob" "Charlie")
A_ROLE=("DEV" "SALES" "QA")
A_STATE=("閒置" "閒置" "閒置") # 閒置, 工作中, 休息中
A_ENERGY=(100 100 100)

# Task
T_NAME=("修復_500錯誤" "向客戶提案" "撰寫測試" "重構資料庫")
T_ROLE=("DEV" "SALES" "QA" "DEV")
T_TOTAL_TICKS=(2 1 2 3)
T_REWARD=(200 100 150 400)
T_PROGRESS=(0 0 0 0)
T_STATE=("待辦" "待辦" "待辦" "待辦") # 待辦, 執行中, 已完成
T_ASSIGNEE=(-1 -1 -1 -1)

# --- 介面渲染 (View) ---
function render_ui() {
    clear
    echo -e "\033[1;36m===================================================\033[0m"
    echo -e "\033[1;33m 🏢 ARCHON 科技公司 - [第一階段：車庫創業]\033[0m"
    echo -e "\033[1;36m===================================================\033[0m"
    echo -e " 💰 \033[1;32m資金: \$${FUNDS}\033[0m   ⭐ \033[1;33m信譽: ${REP}\033[0m   ⏳ \033[1;35m時間: 第 ${TICK} 回合\033[0m"
    echo "---------------------------------------------------"
    echo -e "\033[1m[👥 員工名單]\033[0m"
    for i in "${!A_NAME[@]}"; do
        local state_color="\033[0m"
        if [ "${A_STATE[$i]}" == "閒置" ]; then state_color="\033[0;32m"; fi
        if [ "${A_STATE[$i]}" == "工作中" ]; then state_color="\033[0;31m"; fi
        
        # 為了對齊，使用 printf 的長度控制
        printf " 員工ID:%d | %-7s (%-5s) | 狀態: %b[%-7s]\033[0m | 體力: %d%%\n" "$i" "${A_NAME[$i]}" "${A_ROLE[$i]}" "$state_color" "${A_STATE[$i]}" "${A_ENERGY[$i]}"
    done
    echo "---------------------------------------------------"
    echo -e "\033[1m[📋 待辦與執行中任務]\033[0m"
    local all_completed=true
    for i in "${!T_NAME[@]}"; do
        if [ "${T_STATE[$i]}" != "已完成" ]; then
            all_completed=false
            local assigned=""
            local status_color="\033[0m"
            if [ "${T_STATE[$i]}" == "執行中" ]; then 
                assigned=" -> \033[1;35m負責人: ${A_NAME[${T_ASSIGNEE[$i]}]} [進度: ${T_PROGRESS[$i]}/${T_TOTAL_TICKS[$i]}]\033[0m"
                status_color="\033[0;31m"
            fi
            printf " 任務ID %d: %-15s | 需求: %-5s | 耗時: %d 回合 | 獎金: \$%-3d | 狀態: %b%-7s\033[0m%b\n" "$i" "${T_NAME[$i]}" "${T_ROLE[$i]}" "${T_TOTAL_TICKS[$i]}" "${T_REWARD[$i]}" "$status_color" "${T_STATE[$i]}" "$assigned"
        fi
    done
    if $all_completed; then
        echo -e " \033[1;32m🎉 所有任務皆已完成！恭喜通過第一階段！ 🎉\033[0m"
    fi
    echo -e "\033[1;36m===================================================\033[0m"
    if [ -n "$MSG" ]; then
        echo -e " \033[1;33m>> 系統訊息: $MSG\033[0m"
        echo -e "\033[1;36m===================================================\033[0m"
        MSG="" # 清空訊息
    fi
    echo -e "\033[1m可執行動作:\033[0m"
    echo " [a] 指派任務 (Assign)"
    echo " [n] 下一回合 (Next Tick)"
    echo " [q] 離開遊戲 (Quit)"
    echo -n "請選擇動作: "
}

# --- 邏輯控制器 (Controller) ---
function assign_task() {
    echo ""
    read -p "請輸入 任務ID: " t_id
    read -p "請輸入 員工ID: " a_id

    # 防呆檢查
    if [[ ! "$t_id" =~ ^[0-9]+$ ]] || [[ ! "$a_id" =~ ^[0-9]+$ ]]; then MSG="輸入的 ID 格式無效。"; return; fi
    if [ -z "${T_NAME[$t_id]}" ]; then MSG="找不到該任務。"; return; fi
    if [ -z "${A_NAME[$a_id]}" ]; then MSG="找不到該員工。"; return; fi
    
    if [ "${T_STATE[$t_id]}" != "待辦" ]; then MSG="該任務目前無法指派（不是待辦狀態）。"; return; fi
    if [ "${A_STATE[$a_id]}" != "閒置" ]; then MSG="${A_NAME[$a_id]} 目前不是閒置狀態，無法指派。"; return; fi
    
    if [ "${T_ROLE[$t_id]}" != "${A_ROLE[$a_id]}" ]; then 
        MSG="職業不符防呆觸發！任務需要 ${T_ROLE[$t_id]}，但 ${A_NAME[$a_id]} 是 ${A_ROLE[$a_id]}。"
        return
    fi

    if [ "${A_ENERGY[$a_id]}" -lt 10 ]; then
        MSG="${A_NAME[$a_id]} 太累了，無法工作！請讓他休息。"
        return
    fi

    # 執行指派 (狀態變更)
    A_STATE[$a_id]="工作中"
    T_STATE[$t_id]="執行中"
    T_ASSIGNEE[$t_id]=$a_id
    MSG="成功將任務 [${T_NAME[$t_id]}] 指派給員工 [${A_NAME[$a_id]}]。"
}

function advance_time() {
    ((TICK++))
    local reports=""
    
    # 掃描所有執行中任務
    for i in "${!T_NAME[@]}"; do
        if [ "${T_STATE[$i]}" == "執行中" ]; then
            local a_id=${T_ASSIGNEE[$i]}
            
            # 增加進度，消耗體力
            ((T_PROGRESS[$i]++))
            ((A_ENERGY[$a_id]-=10))
            
            # 檢查是否完成
            if [ "${T_PROGRESS[$i]}" -ge "${T_TOTAL_TICKS[$i]}" ]; then
                T_STATE[$i]="已完成"
                A_STATE[$a_id]="閒置"
                ((FUNDS+=${T_REWARD[$i]}))
                reports+="🎉 恭喜！${A_NAME[$a_id]} 完成了 [${T_NAME[$i]}]！ (入帳: +\$${T_REWARD[$i]})  "
            fi
        fi
    done
    
    if [ -z "$reports" ]; then
        MSG="時間流逝了。大家都在努力工作中..."
    else
        MSG="$reports"
    fi
}

# --- 遊戲主迴圈 (Game Loop) ---
while true; do
    render_ui
    read -n 1 -s action
    
    case $action in
        a|A) assign_task ;;
        n|N) advance_time ;;
        q|Q) clear; echo "遊戲結束。感謝遊玩！"; exit 0 ;;
        *) MSG="未知的動作，請按 a, n 或 q。" ;;
    esac
done
