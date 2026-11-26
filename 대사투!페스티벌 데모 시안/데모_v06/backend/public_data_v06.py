"""공공데이터(공공데이터포털)를 불러와 기획안에 저장할 '시점 값'으로 정리한다.
- 날씨: 기상청 지상(종관, ASOS) 일자료, 대구 관측소(143). 개최일과 같은 날짜의 최근 3년 관측값 (예보가 아님)
- 상권: 소상공인시장진흥공단 상가(상권)정보, 두류공원 중심 반경 안 상가 업종
- 행사: 한국관광공사 국문 관광정보, 가장 최근 해의 같은 시기(앞뒤 2주)에 등록된 대구 행사
인증키(DATA_GO_KR_KEY)는 요청 주소에만 쓰고, 오류 내용이나 기록에는 남기지 않는다."""
import datetime
import json
import os
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

from plan_schema_v06 import schedule_headers

CENTER = {'name': '대구두류공원(관광공사 등록 좌표)', 'lon': '128.5590800', 'lat': '35.8486622'}
RADIUS = 700
HOT = 33.0          # 이 값 이상을 '33℃ 이상인 날'로 센다
STATION = '143'     # 대구
URLS = {'weather': 'https://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList',
        'stores': 'https://apis.data.go.kr/B553077/api/open/sdsc2/storeListInRadius',
        'events': 'https://apis.data.go.kr/B551011/KorService2/searchFestival2'}
NAMES = {'weather': '날씨(기상청)', 'stores': '상권(소상공인시장진흥공단)', 'events': '행사(한국관광공사)'}


class PublicDataError(Exception):
    pass


def _context():
    for path in (os.getenv('SSL_CERT_FILE'), '/etc/ssl/cert.pem'):
        if path and os.path.exists(path):
            return ssl.create_default_context(cafile=path)
    return ssl.create_default_context()


def fetch_json(url, params):
    key = os.getenv('DATA_GO_KR_KEY', '').strip()
    if not key:
        raise PublicDataError('공공데이터 인증키가 설정되지 않았습니다.')
    if '%' in key:
        key = urllib.parse.unquote(key)
    request = urllib.request.Request(url + '?' + urllib.parse.urlencode(dict(params, serviceKey=key)), headers={'User-Agent': 'daesatu-planner'})
    try:
        with urllib.request.urlopen(request, timeout=30, context=_context()) as r:
            return json.loads(r.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e:
        raise PublicDataError('HTTP %s' % e.code) from None
    except ValueError:
        raise PublicDataError('응답 형식 오류') from None
    except Exception as e:
        raise PublicDataError('연결 실패 %s' % type(e).__name__) from None


def _items(body):
    x = (body or {}).get('items')
    if isinstance(x, dict):
        x = x.get('item', [])
    return x if isinstance(x, list) else []


def period_days(period):
    """개최 기간에서 (월, 일) 시작·끝. 날짜를 알 수 없으면 None."""
    labels = schedule_headers(period)
    found = [re.match(r'(\d{1,2})/(\d{1,2})', v) for v in (labels[0], labels[-1])]
    if not all(found):
        return None
    return tuple((int(m[1]), int(m[2])) for m in found)


def _recent_years(end_md, today, n):
    year = today.year
    if datetime.date(year, *end_md) >= today - datetime.timedelta(days=1):
        year -= 1
    return list(range(year - n + 1, year + 1))


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def weather(days, today, fetch):
    start, end = days
    rows = []
    for year in _recent_years(end, today, 3):
        a, b = datetime.date(year, *start), datetime.date(year, *end)
        d = fetch(URLS['weather'], {'dataType': 'JSON', 'dataCd': 'ASOS', 'dateCd': 'DAY', 'startDt': a.strftime('%Y%m%d'),
                                    'endDt': b.strftime('%Y%m%d'), 'stnIds': STATION, 'numOfRows': '31', 'pageNo': '1'})
        items = _items((d.get('response') or {}).get('body'))
        highs = [v for v in (_num(i.get('maxTa')) for i in items) if v is not None]
        if not highs:
            raise PublicDataError('%d년 관측값 없음' % year)
        rains = [_num(i.get('sumRn')) or 0.0 for i in items]
        rows.append([str(year), '%d/%d~%d/%d' % (start[0], start[1], end[0], end[1]), '%.1f' % (sum(highs) / len(highs)), '%.1f' % max(highs),
                     '%d / %d일' % (sum(v >= HOT for v in highs), len(highs)), '%d일 · %.1fmm' % (sum(v > 0 for v in rains), sum(rains))])
    return {'station': '대구 관측소(143)', 'rows': rows}


def stores(fetch):
    d = fetch(URLS['stores'], {'type': 'json', 'radius': str(RADIUS), 'cx': CENTER['lon'], 'cy': CENTER['lat'], 'numOfRows': '1000', 'pageNo': '1'})
    body = d.get('body') or {}
    items = body.get('items') or []
    if not items:
        raise PublicDataError('상가 자료 없음')
    total = int(body.get('totalCount') or len(items))
    large = Counter(i.get('indsLclsNm') or '기타' for i in items)
    food = Counter((i.get('indsMclsNm') or '기타').strip() for i in items if i.get('indsLclsNm') == '음식')
    month = str((d.get('header') or {}).get('stdrYm') or '')
    top = large.most_common(6)
    rows = [[k, str(v)] for k, v in top]
    if sum(large.values()) > sum(v for _, v in top):
        rows.append(['그 밖의 업종', str(sum(large.values()) - sum(v for _, v in top))])
    return {'center': CENTER['name'], 'radius': RADIUS, 'total': str(total), 'counted': str(len(items)),
            'asof': ('%s년 %d월' % (month[:4], int(month[4:6]))) if re.fullmatch(r'\d{6}', month) else '',
            'rows': rows, 'food': [[k, str(v)] for k, v in food.most_common(5)]}


def events(days, today, fetch):
    start, end = days
    year = _recent_years(end, today, 1)[0]
    a = datetime.date(year, *start) - datetime.timedelta(days=14)
    b = datetime.date(year, *end) + datetime.timedelta(days=14)
    d = fetch(URLS['events'], {'MobileOS': 'ETC', 'MobileApp': 'Daesatu', '_type': 'json', 'lDongRegnCd': '27',
                               'eventStartDate': a.strftime('%Y%m%d'), 'numOfRows': '100', 'pageNo': '1', 'arrange': 'A'})
    response = d.get('response') or {}
    if str((response.get('header') or {}).get('resultCode')) != '0000':
        raise PublicDataError('행사 조회 실패')
    found = []
    for i in _items(response.get('body')):
        try:
            s = datetime.datetime.strptime(str(i.get('eventstartdate')), '%Y%m%d').date()
            e = datetime.datetime.strptime(str(i.get('eventenddate')), '%Y%m%d').date()
        except ValueError:
            continue
        if s <= b and e >= a:
            found.append((s, e, str(i.get('title') or '')[:60]))
    rows = [[t, '%d/%d~%d/%d' % (s.month, s.day, e.month, e.day)] for s, e, t in sorted(found)[:10]]
    return {'range': '%d년 %d/%d~%d/%d' % (year, a.month, a.day, b.month, b.day), 'total': str(len(found)), 'rows': rows}


def collect(period, today=None, fetch=fetch_json):
    """(저장할 값, 실패한 항목 설명 목록). 하나가 실패해도 나머지는 담는다."""
    today = today or datetime.date.today()
    days = period_days(period)
    out = {'fetched': today.isoformat(), 'period_key': '|'.join(schedule_headers(period))}
    failed = []
    jobs = [('stores', lambda: stores(fetch))]
    if days:
        jobs = [('weather', lambda: weather(days, today, fetch))] + jobs + [('events', lambda: events(days, today, fetch))]
    else:
        failed.append('개최 기간에 날짜가 없어 날씨·행사는 불러오지 않았습니다.')
    for name, job in jobs:
        try:
            out[name] = job()
        except PublicDataError as e:
            failed.append('%s: %s' % (NAMES[name], e))
        except Exception as e:
            failed.append('%s: 처리 실패 %s' % (NAMES[name], type(e).__name__))
    if not any(k in out for k in NAMES):
        raise PublicDataError(' / '.join(failed) or '불러온 자료가 없습니다.')
    return out, failed


def summary_for_ai(public):
    """설명 글 AI에게 줄 요약. 관측·등록 시점이 있는 과거 자료임을 함께 알린다."""
    if not public:
        return None
    out = {'주의': '모두 조회 시점의 과거·현재 자료다. 개최 연도의 날씨 예보나 행사 일정이 아니다.', '조회일': public.get('fetched')}
    if public.get('weather'):
        out['최근 3년 같은 날짜의 대구 관측값(연도, 날짜, 평균 최고기온, 최고기온 최댓값, 33℃ 이상인 날, 비 온 날·합계)'] = public['weather']['rows']
    if public.get('stores'):
        s = public['stores']
        out['두류공원 반경 %sm 상가(%s 기준)' % (s['radius'], s['asof'])] = {'전체': s['total'], '업종': s['rows'], '음식 세부': s['food']}
    if public.get('events'):
        out['%s 대구 등록 행사' % public['events']['range']] = public['events']['rows']
    return out


def blocks(public, section, period=''):
    """기획안에 넣는 표. section: 'weather' | 'stores' | 'events'."""
    data = (public or {}).get(section)
    if not data:
        return []
    asked = public.get('fetched', '')
    table = lambda rows: {'t': 'table', 'hdr': 'col', 'keep': True, 'rows': rows}   # 짧은 근거 표는 쪽을 나누지 않는다
    note = lambda text: {'t': 'note', 'text': '출처: %s · 조회일 %s' % (text, asked)}
    out = []
    if section == 'weather':
        out = [{'t': 'h3', 'text': '최근 3년 같은 날짜의 대구 날씨 (관측값)'},
               table([['연도', '날짜', '평균 최고(℃)', '가장 높은 기온(℃)', '33℃ 이상', '비 온 날 · 합계']] + data['rows']),
               note('기상청 지상(종관, ASOS) 일자료, %s. 과거 관측값이며 개최 연도의 예보가 아니다' % data['station'])]
    elif section == 'stores':
        out = [{'t': 'h3', 'text': '축제장 주변 상권 (반경 %sm, 상가 %s곳)' % (data['radius'], data['total'])},
               table([['업종(대분류)', '상가 수']] + data['rows'])]
        if data['food']:
            out.append(table([['음식 업종(중분류, 많은 순)', '상가 수']] + data['food']))
        out.append(note('소상공인시장진흥공단 상가(상권)정보%s, 기준점 %s. 영업 여부와 축제 참여 의사는 확인하지 않은 자료다'
                        % ((' (%s 기준)' % data['asof']) if data['asof'] else '', data['center'])))
    else:
        rows = data['rows'] or [['조회된 행사 없음', '-']]
        out = [{'t': 'h3', 'text': '같은 시기 대구 등록 행사 (%s, %s건)' % (data['range'], data['total'])},
               table([['행사명', '기간']] + rows),
               note('한국관광공사 국문 관광정보 서비스. 등록된 행사만 보이며 개최 연도의 일정은 따로 확인해야 한다')]
    return out


def is_stale(public, period):
    return bool(public) and public.get('period_key') != '|'.join(schedule_headers(period))
