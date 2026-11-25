import base64,io,json,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from auth_v06 import Store
from attachments_v06 import Attachments,AttachmentError,MAX_TEXT

def payload(name,raw):return {'name':name,'data':base64.b64encode(raw).decode()}
def office(parts):
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
        for name,text in parts.items():z.writestr(name,text)
    return b.getvalue()

class FileTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(Path(self.tmp.name)/'db.sqlite3');self.files=Attachments(self.store)
    def tearDown(self):self.tmp.cleanup()
    def test_text_korean_csv_and_owned_access(self):
        row=self.files.upload(1,payload('../기획.csv','행사,예산\n별빛,미정'.encode('cp949')))
        self.assertEqual(row['name'],'기획.csv');self.assertIn('별빛',row['text'])
        with self.assertRaises(AttachmentError):self.files.get(2,[row['id']])
        self.assertNotIn('text',self.files.public(row))
    def test_office_formats_extract_real_body_text(self):
        cases=[('a.docx',{'word/document.xml':'<document><body><p><t>자료 속 행사</t></p></body></document>'}),('a.pptx',{'ppt/slides/slide1.xml':'<slide><p><t>자료 속 행사</t></p></slide>'}),('a.hwpx',{'Contents/section0.xml':'<section><p><t>자료 속 행사</t></p></section>'}),('a.xlsx',{'xl/worksheets/sheet1.xml':'<worksheet><sheetData><row><c r="B1" t="inlineStr"><is><t>자료 속 행사</t></is></c></row></sheetData></worksheet>'})]
        for name,parts in cases:self.assertIn('자료 속 행사',self.files.upload(1,payload(name,office(parts)))['text'])
    def test_corrupt_unsupported_and_oversize_rejected(self):
        for name,raw in [('a.exe',b'abc'),('a.hwp',b'abc'),('a.png',b'fake'),('a.pdf',b'fake'),('a.docx',b'broken'),('empty.txt',b'')]:
            with self.assertRaises(AttachmentError):self.files.upload(1,payload(name,raw))
        with self.assertRaises(AttachmentError):self.files.upload(1,{'name':'a.txt','data':'a'*(12*1024*1024)})
        with self.assertRaises(AttachmentError):self.files.upload(1,payload('a.docx',office({'word/document.xml':'<!DOCTYPE a [<!ENTITY b "test">]><a>&b;</a>'})))
    def test_pdf_uses_visual_reader_and_failures_are_not_success(self):
        with patch('attachments_v06.read_visual',return_value='PDF에서 읽은 행사 이름') as read:
            row=self.files.upload(1,payload('계획.pdf',b'%PDF-1.7\nfixture'));read.assert_called_once();self.assertIn('행사 이름',row['text'])
        with patch('attachments_v06.read_visual',side_effect=RuntimeError('private credential')):
            with self.assertRaises(AttachmentError) as e:self.files.upload(1,payload('계획.pdf',b'%PDF-1.7'))
        self.assertNotIn('credential',str(e.exception))
    def test_followup_context_and_explicit_partial_read(self):
        row=self.files.upload(1,payload('긴기획.txt',('첨부근거'*20000).encode()))
        self.assertEqual(len(row['text']),MAX_TEXT);self.assertTrue(row['truncated'])
        w={'messages':[{'role':'user','content':'요약','attachments':[self.files.public(row)]}]}
        context=self.files.context(1,w);self.assertIn('긴기획.txt',context);self.assertIn('첨부근거',context)
        self.assertEqual(self.files.context(2,{'messages':[]}), '')

if __name__=='__main__':unittest.main()
