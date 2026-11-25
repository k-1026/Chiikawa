import sys,unittest,zipfile,io,xml.etree.ElementTree as E
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
import plan_export_v06 as export
MODEL={'title':'한글 단어 보호 검사','sections':[{'h':'1. 프로그램','blocks':[{'t':'table','hdr':'col','rows':[['프로그램','운영 내용'],['지역문화체험','가족 관람객이 지역문화체험 프로그램에 참여하는 계획을 확인합니다.']]},{'t':'table','hdr':'row','rows':[['총 사업비','미입력']]}]}]}
class ExportTests(unittest.TestCase):
 def test_html_keep_words_repeat_header_and_borders(self):
  s=export.model_to_html(MODEL)
  for token in ['word-break:keep-all','overflow-wrap:normal','<thead>','<tbody>','print-color-adjust:exact','break-inside:avoid','border-bottom:1px solid']:self.assertIn(token,s)
 def test_docx_shading_word_wrap_and_full_borders(self):
  z=zipfile.ZipFile(io.BytesIO(export.to_docx(MODEL)));r=E.fromstring(z.read('word/document.xml'));ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};q=lambda n:'{'+ns['w']+'}'+n
  self.assertTrue(r.findall('.//w:shd',ns));self.assertTrue(r.findall('.//w:tblHeader',ns))
  for row in r.findall('.//w:tr',ns):self.assertIsNotNone(row.find('w:trPr/w:cantSplit',ns))
  for cell in r.findall('.//w:tc',ns):self.assertIsNotNone(cell.find('w:tcPr/w:tcBorders/w:bottom',ns))
  for wrap in r.findall('.//w:wordWrap',ns):self.assertEqual(wrap.get(q('val')),'1')
  self.assertTrue(r.findall('.//w:wordWrap',ns))
 def test_hwpx_floating_page_flow_and_shading(self):
  z=zipfile.ZipFile(io.BytesIO(export.to_hwpx(MODEL)));h=E.fromstring(z.read('Contents/header.xml'));s=E.fromstring(z.read('Contents/section0.xml'));ns={'hh':'http://www.hancom.co.kr/hwpml/2011/head','hp':'http://www.hancom.co.kr/hwpml/2011/paragraph','hc':'http://www.hancom.co.kr/hwpml/2011/core'}
  for b in h.findall('.//hh:breakSetting',ns):self.assertEqual(b.get('breakNonLatinWord'),'KEEP_WORD')
  self.assertTrue(h.findall('.//hc:winBrush[@faceColor="#EEE8F7"]',ns))
  for tb in s.findall('.//hp:tbl',ns):self.assertEqual(tb.find('hp:pos',ns).get('treatAsChar'),'0');self.assertEqual(tb.get('pageBreak'),'CELL')
  self.assertEqual(s.find('.//hp:tbl',ns).get('repeatHeader'),'1')
