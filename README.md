# myblog_publish

> **MyBlog + Music Review** 프로젝트의 발행 서비스 — 글 저장 후 정적 사이트를 갱신하는 퍼블리싱 전용 Lambda

🔗 **전체 프로젝트 README:** [MyBlog + Music Review](https://github.com/hyuntohoon/myblog_front#관련-리포지토리)

---

## 개요

"DB에 글 저장" 이후 **정적 사이트를 갱신(발행)**하는 전용 서비스입니다. Front의 글쓰기 UI에서 발행을 요청하면, GitHub 리포에 MDX 파일을 커밋하고 GitHub Actions를 트리거하여 Astro 빌드·배포를 수행합니다.

---

## 발행 흐름

```
관리자가 글 저장 완료
  ↓
Front → POST /publish 호출
  ↓
Publish Lambda
  ├── GitHub API로 MDX/콘텐츠 파일 생성·갱신 (커밋)
  └── GitHub Actions 워크플로우 트리거
  ↓
GitHub Actions
  ├── Astro 빌드
  ├── S3 업로드
  └── CloudFront invalidation
  ↓
정적 사이트 갱신 완료
```

---

## 핵심 설계

**글 저장과 발행의 분리** — "DB 트랜잭션(글 저장)"과 "외부 연동(GitHub → S3 배포)"은 실패 지점과 재시도 방식이 완전히 다릅니다. 한 서비스에 섞으면 트랜잭션·운영 복잡도가 폭발합니다.

- 글 저장(Backend): DB 트랜잭션으로 즉시 완결, 빠름
- 발행(Publish): 외부 API 호출(GitHub), 빌드 시간 필요, 지연 가능

**보안 경계** — GitHub API 토큰, Actions 트리거 권한 등 외부 연동 시크릿이 이 서비스에만 존재합니다. Backend나 Music API에 노출되지 않습니다.

---

## 기술 스택

| 항목      | 기술                                        |
| --------- | ------------------------------------------- |
| 배포      | AWS Lambda + API Gateway                    |
| 외부 연동 | GitHub API (Contents API / Actions trigger) |
| 정적 빌드 | GitHub Actions + Astro                      |
| 정적 서빙 | S3 + CloudFront                             |

---

## 환경 변수

| 변수            | 설명                         |
| --------------- | ---------------------------- |
| `GITHUB_TOKEN`  | GitHub API 접근 토큰         |
| `GITHUB_REPO`   | 대상 리포지토리 (owner/repo) |
| `GITHUB_BRANCH` | 커밋 대상 브랜치             |
| `AWS_REGION`    | AWS 리전                     |

---

## 왜 분리했는가

"글 저장(DB)"과 "정적 배포(S3/CloudFront)"는 **실패 지점·재시도 방식이 완전히 다릅니다**. 한 서비스에 섞으면 트랜잭션·운영 복잡도가 폭발합니다. 외부 연동(GitHub API/Actions)과 권한(GitHub token)이 필요해서 보안 경계도 뚜렷합니다. 발행 파이프라인을 독립시키면:

- 글 저장은 빠르게 끝내고
- 발행은 비동기·재시도·관측이 쉬워짐
- 향후 Outbox/publishing_runs를 붙이기에 최적의 위치

---

## 향후 개선

- **Outbox 패턴** — publish 이벤트를 DB에 기록하여 발행 상태 추적 (queued → running → success/fail)
- **`publishing_runs` 테이블** — 발행 이력·실패 재시도·알림
- **CloudFront invalidation 최적화** — 변경 경로만 무효화하여 비용·횟수 절감

---

## 관련 리포지토리

| 리포                                                             | 역할                          |
| ---------------------------------------------------------------- | ----------------------------- |
| [`myblog_front`](https://github.com/hyuntohoon/myblog_front)     | 정적 사이트 + 글쓰기 UI       |
| [`myblog_backend`](https://github.com/hyuntohoon/myblog_backend) | 글·카테고리 API + 인증        |
| [`myblog_music`](https://github.com/hyuntohoon/myblog_music)     | DB-first 검색 + Sync 트리거   |
| [`myblog_worker`](https://github.com/hyuntohoon/myblog_worker)   | SQS Consumer + Spotify 동기화 |
| **myblog_publish** (현재)                                        | 정적 사이트 발행              |
