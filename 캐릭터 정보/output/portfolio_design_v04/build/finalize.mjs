import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url));
const skill='/Users/seunghui/.codex/plugins/cache/openai-primary-runtime/presentations/26.1119.11507/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
const out=path.join(dir,'../deliverables');await fs.mkdir(out,{recursive:true});
const result=await finalizePresentation({workspaceDir:path.resolve(dir,'..'),candidatePath:path.join(dir,'candidate_compact.pptx'),finalPath:path.join(out,'대구_얼라들_포트폴리오_디자인반영_v04.pptx'),pythonExecutable:'/Users/seunghui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','18288000,10287000','--validate-bullet-geometry','--validate-heading-fit'],explicitTotalSlideCount:26,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],fontPolicy:{basis:'design',families:['Apple SD Gothic Neo']},verifyArtifactToolImport:true,receiptPath:path.join(dir,'validation.json')});
console.log(JSON.stringify(result,null,2));
