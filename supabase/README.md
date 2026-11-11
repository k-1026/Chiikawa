# Supabase·Vercel 연습 배포 가이드

2027 대구 사투리 축제 안내 페이지를 DB에 올리고 인터넷에 배포하는 순서예요.

| 파일 | 하는 일 | 어디서 실행 |
|---|---|---|
| `schema.sql` | 표 16개와 공개 권한 만들기 | Supabase SQL Editor |
| `seed.sql` | 표에 내용 넣기 | Supabase SQL Editor |

## 먼저 알아 둘 것

**schema와 seed는 Vercel에 넣는 파일이 아니에요.** Supabase에서 한 번 실행하면 끝이에요.

```
[GitHub 코드] → [Vercel: 페이지를 인터넷에 올림] → [방문자 브라우저]
                                                       ↓ 내용 요청
                                                 [Supabase: DB]
```

- Supabase는 **내용**을 보관하고, Vercel은 **페이지**를 보여 줘요.
- 둘을 잇는 것은 페이지 코드 안의 **프로젝트 URL과 공개 키**예요.
- ⚠ 지금 `index.html`은 내용이 코드에 직접 적혀 있어요. DB를 읽게 바꾸는 작업이 끝나야 DB 내용이 화면에 나와요(4단계).

## 1단계. Supabase 프로젝트 만들기

1. <https://supabase.com> 로그인 → **New project**
2. 이름을 정하고 Region은 **Seoul**(`ap-northeast-2`)을 골라요.
3. DB 비밀번호는 안전한 곳에 저장해요. Git이나 채팅에 적지 마세요.
4. 생성이 끝날 때까지 1~2분 기다려요.

## 2단계. schema → seed 순서로 실행

**순서를 꼭 지켜요. seed를 먼저 실행하면 오류가 나요.**

1. 왼쪽 메뉴 **SQL Editor** → **New query**
2. `schema.sql` 내용을 **전부** 복사해 붙여넣고 **Run**
3. `Success. No rows returned`가 나오면 성공이에요.
4. 새 쿼리를 열어 `seed.sql` 내용을 **전부** 붙여넣고 **Run**
5. 데이터를 지운다는 확인 창이 뜨면 실행을 눌러요. `seed.sql` 맨 위의 `truncate` 때문에 뜨는 창이고, 다시 채우는 동작이라 정상이에요.

## 3단계. 잘 들어갔는지 확인

SQL Editor에서 실행해요.

```sql
select 'festivals' as 표, count(*) as 건수 from public.festivals
union all select 'schedule_items', count(*) from public.schedule_items
union all select 'debate_matches', count(*) from public.debate_matches
union all select 'quiz_options', count(*) from public.quiz_options
union all select 'faq_entries', count(*) from public.faq_entries;
```

정상 결과는 다음과 같아요.

| 표 | 건수 |
|---|---:|
| festivals | 1 |
| schedule_items | 23 |
| debate_matches | 15 |
| quiz_options | 15 |
| faq_entries | 9 |

그다음 웹사이트가 쓰는 방식으로도 읽어 봐요. 대시보드의 API 키 메뉴에서 **프로젝트 URL**과 **Publishable key**(예전 프로젝트는 **anon key**)를 찾아 아래에 넣어요.

```bash
curl "https://프로젝트ID.supabase.co/rest/v1/menu_items?select=name&limit=3" -H "apikey: 공개키"
```

메뉴 3개가 JSON으로 나오면 성공이에요.

### 키 구분

| 키 | 페이지에 넣어도 되나 |
|---|---|
| Publishable key / anon key | ✅ 됩니다. 이 DB는 읽기만 허용해요 |
| Secret key / service_role key | ❌ 절대 안 됩니다. 모든 권한을 가진 키라 GitHub에도 올리면 안 돼요 |

## 4단계. 페이지가 DB를 읽게 바꾸기

`index.html` 안에 직접 적힌 시간표·메뉴·퀴즈 내용을 Supabase에서 불러오도록 바꾸는 단계예요. 프로젝트 URL과 공개 키가 필요해요.

공개 키는 페이지 코드에 직접 적어요. 빌드 과정이 없는 HTML 페이지는 Vercel 환경 변수를 읽지 못해요.

## 5단계. Vercel에 배포

1. <https://vercel.com> 에 GitHub 계정으로 로그인 → **Add New → Project**
2. `k-1026/Chiikawa` 저장소를 가져와요(Import). 안 보이면 저장소 소유자에게 권한을 받거나, 연습용 저장소를 따로 만들어요.
3. 설정을 이렇게 맞춰요.

| 항목 | 값 |
|---|---|
| Framework Preset | **Other** |
| Root Directory | `index.html`이 있는 폴더 |
| Build Command | 비워 둠 |
| Output Directory | 비워 둠 |

4. **Deploy** → 완료되면 `https://프로젝트이름.vercel.app` 주소가 나와요.
5. 그 주소가 누구나 들어올 수 있는 링크예요. 이후에는 연결한 브랜치에 푸시할 때마다 자동으로 다시 배포돼요.

### 브랜치와 폴더 주의

Vercel은 **GitHub에 푸시된 내용**만 봐요. 내 컴퓨터에만 있는 파일은 배포되지 않아요.

| 브랜치 | 안내 페이지 위치 | 상태 |
|---|---|---|
| `main` | `local 리서치/2027/안내페이지` | 푸시되어 있음 |
| `minju` | `local리서치v2/2027/안내페이지` | **아직 커밋 안 됨** |

- 어느 브랜치로 배포할지 정하고, 그 브랜치에 `index.html`과 `assets/`가 있는지 확인해요.
- `supabase/` 폴더는 Root Directory 바깥이라 페이지와 함께 공개되지 않아요.
- 폴더 이름의 한글이나 띄어쓰기 때문에 Root Directory 설정이 안 되면, 영어 이름 폴더(예: `web/`)로 옮겨요.

## 오류가 나면

| 보이는 오류 | 원인 | 해결 |
|---|---|---|
| `relation "public.festivals" does not exist` | seed를 schema보다 먼저 실행 | `schema.sql` 실행 후 다시 `seed.sql` |
| `syntax error at or near ...` | 복사가 잘렸거나 일부만 선택됨 | 에디터를 비우고 파일 전체를 다시 붙여넣기. 일부를 드래그한 채 Run 하지 않기 |
| `permission denied for table ...` (42501) | 읽기 권한이 없음 | `schema.sql` 다시 실행 |
| 페이지에서 쓰기가 42501로 막힘 | 정상. 지금은 읽기만 허용 | 쓰기가 필요하면 표와 정책을 따로 설계 |
| 오류 없이 결과가 `[]` | seed 미실행, 또는 RLS 정책 문제 | 3단계 건수 확인 → 0이면 `seed.sql`, 있으면 `schema.sql` 다시 실행 |
| `Invalid API key` | 키를 잘못 복사했거나 다른 프로젝트 키 | API 키 메뉴에서 다시 복사 |
| 컬럼을 고쳤는데 반영이 안 됨 | `schema.sql`은 이미 있는 표를 바꾸지 않음 | 아래 "처음부터 다시" 실행 |
| 표를 고쳤는데 API에서 `schema cache` 오류 | Supabase가 새 구조를 아직 모름 | SQL Editor에서 `notify pgrst, 'reload schema';` 실행 |
| Vercel `404: NOT_FOUND` | Root Directory가 틀림 | `index.html`이 있는 폴더로 지정하고 Redeploy |
| Vercel에서 이미지만 안 보임 | `assets/`가 푸시 안 됐거나 경로·대소문자가 다름 | GitHub에 `assets/`가 있는지 확인 |
| Vercel에 예전 화면이 나옴 | 다른 브랜치에 푸시함 | Vercel의 Production Branch와 푸시한 브랜치 비교 |

### 처음부터 다시

⚠ 표와 데이터가 모두 지워져요. 연습 중일 때만 쓰세요. 실행한 뒤 2단계를 다시 해요.

```sql
drop table if exists
  public.faq_entries, public.dialect_rules, public.quiz_grades, public.quiz_options,
  public.quiz_questions, public.benefits, public.menu_items, public.debate_matches,
  public.debate_teams, public.debate_topics, public.schedule_items, public.programs,
  public.map_pois, public.zones, public.mascots, public.festivals
cascade;
```

## 내용을 고칠 때

- `seed.sql`을 고쳐 다시 실행해요. 실행하면 표 내용 전체가 다시 채워져요.
- Supabase 화면에서 직접 고친 내용은 `seed.sql`을 다시 실행할 때 사라져요.
- `schema.sql`, `seed.sql`에 비밀번호나 Secret key를 적지 마세요.

## 표 구성

| 묶음 | 표 |
|---|---|
| 축제 | `festivals`, `mascots` |
| 구역·지도 | `zones`, `map_pois` |
| 프로그램 | `programs`, `schedule_items` |
| 토론 대회 | `debate_topics`, `debate_teams`, `debate_matches` |
| 먹거리·혜택 | `menu_items`, `benefits` |
| 능력고사 | `quiz_questions`, `quiz_options`, `quiz_grades` |
| 변환기·도우미 | `dialect_rules`, `faq_entries` |

체크인, 스탬프, 관객 투표, 숙박 인증 표는 만들지 않았어요. 방문자가 저장하는 데이터는 쓰기 권한과 개인정보 보호 설계가 먼저 필요해요(지침 10장). 지금 페이지의 해당 기능은 저장되지 않는 데모예요.

## 참고

- [Supabase: 새 표가 Data API에 자동 공개되지 않는 변경](https://supabase.com/changelog/45329-breaking-change-tables-not-exposed-to-data-and-graphql-api-automatically)
- [Supabase: API 보안](https://supabase.com/docs/guides/api/securing-your-api)
- [Vercel: 빌드 설정](https://vercel.com/docs/builds/configure-a-build)
