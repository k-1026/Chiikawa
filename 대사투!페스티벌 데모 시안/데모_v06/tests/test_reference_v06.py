import json,shutil,subprocess,unittest
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]

class ReferenceLoadTests(unittest.TestCase):
    def test_view_guard_precedes_remote_styles_and_body(self):
        html=(ROOT/'reference_v06.html').read_text()
        guard=html.index('id="v06-reference-guard"')
        select=html.index('id="v06-reference-select"')
        self.assertLess(guard,html.index('<link'))
        self.assertLess(select,html.index('<body'))
        css=html[html.rfind('<style',0,guard):html.index('</style>',guard)]
        self.assertIn('html .hero',css)
        self.assertIn('display:none!important',css)
        self.assertIn('html[data-page="map"] #map',css)
        self.assertIn('html[data-page="shop"] #shop',css)
        self.assertNotIn('body[data-page=',html)

    @unittest.skipUnless(shutil.which('node'),'Node is needed for browser bootstrap regression checks')
    def test_early_selector_works_before_body_exists(self):
        html=(ROOT/'reference_v06.html').read_text();a=html.index('<script id="v06-reference-select">')
        script=html[html.index('>',a)+1:html.index('</script>',a)]
        for hash_value,expected in [('#map','map'),('#shop','shop'),('','map')]:
            harness="const vm=require('node:vm');const c={document:{documentElement:{dataset:{}}},location:{hash:"+json.dumps(hash_value)+"},addEventListener:(n,f)=>{c.change=f}};vm.createContext(c);vm.runInContext("+json.dumps(script)+",c);const first=c.document.documentElement.dataset.page;c.location.hash='#shop';c.change();process.stdout.write(JSON.stringify([first,c.document.documentElement.dataset.page]));"
            out=subprocess.run(['node','-e',harness],check=True,capture_output=True,text=True)
            self.assertEqual(json.loads(out.stdout),[expected,'shop'])

    @unittest.skipUnless(shutil.which('node'),'Node is needed for reference JavaScript checks')
    def test_reference_scripts_parse_after_guard_move(self):
        class Scripts(HTMLParser):
            def __init__(self):super().__init__();self.inside=False;self.scripts=[]
            def handle_starttag(self,tag,attrs):
                if tag=='script':self.inside=True;self.scripts.append('')
            def handle_endtag(self,tag):
                if tag=='script':self.inside=False
            def handle_data(self,data):
                if self.inside:self.scripts[-1]+=data
        parser=Scripts();parser.feed((ROOT/'reference_v06.html').read_text())
        self.assertEqual(len(parser.scripts),3)
        for script in parser.scripts:
            out=subprocess.run(['node','--check'],input=script,capture_output=True,text=True)
            self.assertEqual(out.returncode,0,out.stderr)

if __name__=='__main__':unittest.main()
