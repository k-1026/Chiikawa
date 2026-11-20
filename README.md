# 깃 명령어 메뉴얼 (복습용)

> 배운 내용을 점검하고, 팀 프로젝트에서 자주 막히는 부분까지 채운 복습용 메뉴얼이에요.
> 팀원과 먼저 맞출 것은 **5장 브랜치 이름 규칙**과 **10장 커밋 메시지 규칙**이에요. 이 두 장은 그대로 공유하면 돼요.

---

## 목차

1. [Git 기본 개념](#1-git-기본-개념)
2. [처음 한 번만 하는 설정](#2-처음-한-번만-하는-설정)
3. [GitHub 인증 (PAT / SSH)](#3-github-인증-pat--ssh)
4. [기본 흐름: status → add → commit](#4-기본-흐름-status--add--commit)
5. [브랜치 + 이름 규칙](#5-브랜치--이름-규칙)
6. [push / pull (새 브랜치 첫 push 포함)](#6-push--pull)
7. [Pull Request(PR)로 합치기](#7-pull-requestpr로-합치기)
8. [충돌(Conflict) 해결](#8-충돌conflict-해결)
9. [되돌리기 상황별 표](#9-되돌리기-상황별-표)
10. [커밋 메시지 규칙](#10-커밋-메시지-규칙)
11. [.gitignore와 비밀 키 관리](#11-gitignore와-비밀-키-관리)
12. [자주 나는 에러 8개 + 해결법](#12-자주-나는-에러-8개--해결법)
13. [복습 퀴즈 10문제](#13-복습-퀴즈-10문제)

---

## 1. Git 기본 개념

| 용어 | 뜻 |
|---|---|
| 저장소(repository) | Git이 관리하는 프로젝트 폴더. 숨김 폴더 `.git`에 모든 기록이 들어 있어요 |
| 작업 폴더(working tree) | 지금 Finder에서 보이는 파일. **현재 체크아웃한 브랜치의 파일만** 보여요 |
| 스테이징(staging) | `git add`로 "다음 커밋에 넣을 것"을 담아두는 곳 |
| 커밋(commit) | 스테이징한 변경을 하나의 기록으로 저장한 것 |
| 원격(remote, `origin`) | GitHub에 있는 저장소 |
| 브랜치(branch) | 작업을 나눠서 진행하는 독립된 줄기 |

```
작업 폴더 --(git add)--> 스테이징 --(git commit)--> 로컬 저장소 --(git push)--> GitHub
```

---

## 2. 처음 한 번만 하는 설정

```bash
git config --global user.name "내이름"
git config --global user.email "내이메일@example.com"
git config --global init.defaultBranch main
```

```bash
git clone https://github.com/계정/저장소.git   # 기존 저장소 복사
git init                                        # 새 폴더를 저장소로 만들기
```

---

## 3. GitHub 인증 (PAT / SSH)

> ⚠️ **GitHub 비밀번호로는 push가 안 돼요.** 첫 push 때 거의 무조건 여기서 막혀요.

### 방법 A. PAT(Personal Access Token)

1. GitHub → Settings → Developer settings → Personal access tokens → **Generate new token**
2. 권한(scope)은 저장소 쓰기가 가능하도록 선택하고, 만료일을 정해요
3. push할 때 비밀번호 칸에 **토큰을 붙여넣어요**
4. 맥에서는 키체인에 저장돼서 다음부터는 자동으로 들어가요

### 방법 B. SSH 키

```bash
ssh-keygen -t ed25519 -C "내이메일@example.com"   # 키 만들기
cat ~/.ssh/id_ed25519.pub                         # 공개키 복사
```

1. GitHub → Settings → SSH and GPG keys → **New SSH key**에 공개키를 붙여넣어요
2. 연결 확인: `ssh -T git@github.com`
3. 저장소 주소를 SSH로 바꿔요: `git remote set-url origin git@github.com:계정/저장소.git`

> 토큰과 개인키(`id_ed25519`, `.pub`가 없는 파일)는 **절대 공유하거나 커밋하지 마세요.**

---

## 4. 기본 흐름: status → add → commit

```bash
git status                  # 지금 상태 확인 (가장 자주 쓰는 명령어)
git add 파일명              # 특정 파일 스테이징
git add .                   # 현재 폴더 전체 스테이징
git commit -m "메시지"      # 커밋
git log --oneline --graph   # 기록 한 줄씩 보기
```

### ✏️ 정정: `git diff`가 보여주는 범위

| 명령어 | 보여주는 것 |
|---|---|
| `git diff` | **add 안 한** 변경만 |
| `git diff --staged` | **add 한** (스테이징된) 변경 |
| `git diff HEAD` | add 여부와 상관없이 마지막 커밋 이후 전체 변경 |

> `git diff`는 "커밋 안 한 변경"이 아니라 "**add 안 한** 변경"이에요.

---

## 5. 브랜치 + 이름 규칙

```bash
git branch                     # 로컬 브랜치 목록 (* 표시가 현재 브랜치)
git branch -a                  # 원격 브랜치까지 모두
git switch 브랜치명            # 브랜치 이동 (= git checkout 브랜치명)
git switch -c 새브랜치명       # 새로 만들고 바로 이동 (= git checkout -b)
git branch -d 브랜치명         # 합쳐진 브랜치 삭제
```

> 💡 브랜치를 바꾸면 Finder에 보이는 파일도 바뀌어요. 다른 브랜치의 파일은 삭제된 게 아니라 `.git` 안에 보관돼 있어요.
> 💡 브랜치 이동 전에는 커밋하거나 `git stash`로 변경을 잠깐 치워두세요.

### 📌 팀 브랜치 이름 규칙 (팀원과 맞출 것)

| 규칙 | 예시 | 용도 |
|---|---|---|
| `main` | `main` | 최종본. 직접 커밋하지 않고 PR로만 합쳐요 |
| `이름` | `minju` | 개인 작업 공간 (지금 팀에서 쓰는 방식) |
| `feature/작업내용` | `feature/popup-research` | 기능·자료 단위 작업 |
| `fix/고칠내용` | `fix/typo-guide` | 오류 수정 |
| `docs/문서내용` | `docs/git-manual` | 문서 작업 |

- 영어 소문자와 `-`를 써요 (한글·띄어쓰기는 피하기)
- 한 브랜치에는 한 가지 작업만 담아요

---

## 6. push / pull

```bash
git pull                     # 원격 변경 가져와서 합치기 (fetch + merge)
git fetch                    # 원격 변경만 가져오기 (합치지는 않음)
git push                     # 내 커밋 올리기
```

### ⚠️ 새 브랜치 첫 push

새로 만든 브랜치는 GitHub에 아직 없어서 그냥 `git push` 하면 에러가 나요.

```bash
git push -u origin feature/popup-research
```

- `-u`(upstream)는 "이 로컬 브랜치 = 원격의 이 브랜치"라고 연결해줘요
- **한 번만** 하면 다음부터는 `git push`, `git pull`만 써도 돼요

> 💡 push 전에는 항상 `git pull`을 먼저 해서 최신 상태로 맞추세요.

---

## 7. Pull Request(PR)로 합치기

> 팀 프로젝트에서는 로컬 `git merge`보다 **GitHub에서 PR로 합치는 게 기본**이에요. 누가 뭘 바꿨는지 리뷰하고 기록을 남길 수 있어요.

1. 내 브랜치에서 작업 → 커밋 → `git push -u origin 내브랜치`
2. GitHub 저장소 → **Compare & pull request** 클릭
3. base: `main` ← compare: `내브랜치` 확인
4. 제목과 설명(무엇을, 왜 바꿨는지)을 쓰고 **Create pull request**
5. 팀원이 리뷰 → 승인 → **Merge pull request**
6. 합친 뒤 내 컴퓨터 정리:

```bash
git switch main
git pull
git branch -d 내브랜치     # 다 쓴 브랜치면 삭제
```

GitHub CLI(`gh`)를 쓰면 터미널에서도 만들 수 있어요: `gh pr create`

---

## 8. 충돌(Conflict) 해결

같은 파일의 같은 부분을 두 사람이 다르게 고치면 충돌이 나요.

### 충돌 표시 읽는 법

```
<<<<<<< HEAD
내가 쓴 내용 (현재 브랜치)
=======
상대가 쓴 내용 (합치려는 브랜치)
>>>>>>> feature/popup-research
```

### 해결 순서

1. `git status`로 충돌난 파일을 확인해요 (`both modified`)
2. 파일을 열어 **남길 내용만 남기고** `<<<<<<<`, `=======`, `>>>>>>>` 줄을 모두 지워요
3. 저장 후:

```bash
git add 충돌파일
git commit                 # merge 커밋 완료
```

### 일단 취소하고 싶을 때

```bash
git merge --abort          # merge 하기 전 상태로 되돌리기
git rebase --abort         # rebase 중이었다면
```

> 💡 충돌을 줄이려면 자주 `git pull`하고, 작업 단위를 작게 나누고, 같은 파일을 동시에 고치지 않도록 미리 나눠요.

---

## 9. 되돌리기 상황별 표

> 🔑 **핵심: push 했으면 `revert`, push 안 했으면 `reset`**
> 이미 공유된 기록을 `reset`으로 지우면 팀원 기록과 꼬여요.

| 상황 | 명령어 | 결과 |
|---|---|---|
| 파일 수정을 버리고 싶음 (add 전) | `git restore 파일명` | 마지막 커밋 상태로 되돌림 ⚠️ 수정 내용 사라짐 |
| add를 취소하고 싶음 | `git restore --staged 파일명` | 스테이징만 취소, 수정 내용은 남음 |
| 마지막 커밋 메시지만 고치고 싶음 (push 전) | `git commit --amend -m "새 메시지"` | 커밋 덮어쓰기 |
| 마지막 커밋 취소, 변경은 스테이징에 유지 (push 전) | `git reset --soft HEAD~1` | 다시 커밋 가능 |
| 마지막 커밋 취소, 변경은 작업 폴더에 유지 (push 전) | `git reset HEAD~1` | 기본값(`--mixed`) |
| 마지막 커밋과 변경 모두 버림 (push 전) | `git reset --hard HEAD~1` | ⚠️ 변경 내용 영구 삭제 |
| **이미 push한 커밋**을 되돌리고 싶음 | `git revert 커밋ID` | 되돌리는 새 커밋을 만듦 (기록 보존) |
| 작업 중인 걸 잠깐 치워두고 싶음 | `git stash` / `git stash pop` | 임시 보관 / 다시 꺼내기 |

---

## 10. 커밋 메시지 규칙

### 형식

```
타입: 무엇을 했는지 (한 줄, 50자 이내)

(선택) 왜 했는지, 자세한 설명
```

### 📌 타입 (팀원과 맞출 것)

| 타입 | 언제 | 예시 |
|---|---|---|
| `feat:` | 새 기능·새 자료 추가 | `feat: 팝업스토어 자료조사 추가` |
| `fix:` | 오류·오타 수정 | `fix: 상업연계 표 수치 오타 수정` |
| `docs:` | 문서·메뉴얼 수정 | `docs: 깃 명령어 메뉴얼 추가` |
| `refactor:` | 내용은 같고 구조만 정리 | `refactor: 리서치 폴더 구조 정리` |
| `chore:` | 설정·잡무 | `chore: .gitignore에 .DS_Store 추가` |

- 한 커밋에는 한 가지 변경만 담아요
- "수정", "업데이트"처럼 뭘 했는지 모르는 메시지는 피해요

---

## 11. .gitignore와 비밀 키 관리

> ⚠️ **`.gitignore`는 첫 커밋 전에 만드세요.** 이미 커밋된 파일은 `.gitignore`에 추가해도 계속 추적돼요.

### 기본 예시

```gitignore
# macOS
.DS_Store

# 비밀 키
.env
*.key

# 파이썬
__pycache__/
.venv/
```

### 이미 커밋한 파일을 추적에서 빼기

```bash
git rm --cached 파일명      # 파일은 남기고 Git 추적만 해제
git commit -m "chore: 파일명 추적 해제"
```

### 🚨 `.env`(API 키)를 이미 GitHub에 올렸다면

1. **키부터 재발급(폐기 후 새로 발급)** ← 이게 정답이에요
2. 그다음 `.gitignore`에 추가하고 `git rm --cached .env`

> 커밋을 지워도 기록·포크·캐시에 남아 있을 수 있어요. **올라간 키는 이미 유출된 것으로 보고** 반드시 재발급하세요.

---

## 12. 자주 나는 에러 8개 + 해결법

| # | 에러 메시지 (일부) | 원인 | 해결 |
|---|---|---|---|
| 1 | `Support for password authentication was removed` | 비밀번호로 push 시도 | PAT 또는 SSH 사용 (3장) |
| 2 | `The current branch ... has no upstream branch` | 새 브랜치 첫 push | `git push -u origin 브랜치명` |
| 3 | `! [rejected] ... (fetch first)` / `non-fast-forward` | 원격에 내가 없는 커밋이 있음 | `git pull` 후 다시 `git push` |
| 4 | `CONFLICT (content): Merge conflict in 파일` | 같은 부분을 다르게 수정 | 8장 순서대로 해결, 또는 `git merge --abort` |
| 5 | `Your local changes ... would be overwritten by checkout` | 커밋 안 한 변경이 있는 채로 브랜치 이동 | 커밋하거나 `git stash` 후 이동 |
| 6 | `fatal: not a git repository` | Git 저장소가 아닌 폴더에서 실행 | 프로젝트 폴더로 `cd` 하거나 `git init` |
| 7 | `error: src refspec main does not match any` | 커밋이 하나도 없거나 브랜치명이 다름 | 먼저 커밋하고, `git branch`로 이름 확인 |
| 8 | `fatal: refusing to merge unrelated histories` | 기록이 서로 다른 두 저장소를 합치려 함 | 의도한 게 맞으면 `git pull origin main --allow-unrelated-histories` |

---

## 13. 복습 퀴즈 10문제

**Q1.** GitHub에 push할 때 비밀번호 대신 쓰는 두 가지는?
<details><summary>정답</summary>

PAT(Personal Access Token) 또는 SSH 키

</details>

**Q2.** `git diff`와 `git diff --staged`의 차이는?
<details><summary>정답</summary>

`git diff`는 add 안 한 변경, `git diff --staged`는 add 한 변경을 보여줘요.

</details>

**Q3.** 새로 만든 `feature/login` 브랜치를 처음 GitHub에 올리는 명령어는?
<details><summary>정답</summary>

`git push -u origin feature/login`

</details>

**Q4.** 이미 push한 커밋을 되돌릴 때 `reset` 대신 쓰는 명령어와 그 이유는?
<details><summary>정답</summary>

`git revert 커밋ID`. 공유된 기록을 지우지 않고 되돌리는 새 커밋을 만들어서 팀원 기록과 꼬이지 않아요.

</details>

**Q5.** 충돌 표시 `<<<<<<<`와 `=======` 사이에 있는 내용은 누구 것?
<details><summary>정답</summary>

현재 브랜치(HEAD), 즉 내 쪽 내용이에요.

</details>

**Q6.** merge 중 충돌이 났는데 일단 없던 일로 하고 싶다면?
<details><summary>정답</summary>

`git merge --abort`

</details>

**Q7.** `.env`를 실수로 GitHub에 올렸다. 가장 먼저 할 일은?
<details><summary>정답</summary>

그 안의 키를 폐기하고 재발급하는 것. 그다음 `.gitignore` 추가와 `git rm --cached .env`를 해요.

</details>

**Q8.** add한 파일을 스테이징에서만 빼고 수정 내용은 남기려면?
<details><summary>정답</summary>

`git restore --staged 파일명`

</details>

**Q9.** "팝업스토어 표의 오타를 고쳤다"를 커밋 메시지 규칙대로 쓰면?
<details><summary>정답</summary>

`fix: 팝업스토어 표 오타 수정`

</details>

**Q10.** 팀 프로젝트에서 내 브랜치 작업을 `main`에 합치는 기본 방법은?
<details><summary>정답</summary>

GitHub에서 Pull Request(PR)를 만들어 리뷰 후 Merge해요.

</details>

---

## ✅ 그래서 뭐 하면 돼?

팀원들과 **브랜치 이름 규칙(5장)**과 **커밋 메시지 규칙(10장)**만 먼저 맞춰두면 돼요. 두 장을 그대로 공유하면 끝이에요 👍
