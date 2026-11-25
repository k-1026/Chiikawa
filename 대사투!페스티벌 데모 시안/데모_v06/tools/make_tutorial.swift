import AppKit
import AVFoundation
import CoreVideo

// Reproducible, offline instructional animation. All data is explicitly fictional.
let out = CommandLine.arguments[1]
let W=1280, H=720, fps=10
let purple=NSColor(calibratedRed:0.39,green:0.25,blue:0.75,alpha:1)
let ink=NSColor(calibratedRed:0.15,green:0.14,blue:0.23,alpha:1)
let muted=NSColor(calibratedRed:0.45,green:0.43,blue:0.51,alpha:1)
let light=NSColor(calibratedRed:0.95,green:0.93,blue:0.98,alpha:1)
func rect(_ x:Double,_ y:Double,_ w:Double,_ h:Double)->NSRect{NSRect(x:x,y:Double(H)-y-h,width:w,height:h)}
func box(_ x:Double,_ y:Double,_ w:Double,_ h:Double,_ color:NSColor,_ radius:Double=16){color.setFill();NSBezierPath(roundedRect:rect(x,y,w,h),xRadius:radius,yRadius:radius).fill()}
func text(_ s:String,_ x:Double,_ y:Double,_ w:Double,_ size:Double=24,_ color:NSColor=ink,_ bold:Bool=false,_ h:Double=80){let style=NSMutableParagraphStyle();style.lineSpacing=7;let font=NSFont(name:bold ? "AppleSDGothicNeo-Bold":"AppleSDGothicNeo-Regular",size:size) ?? NSFont.systemFont(ofSize:size);(s as NSString).draw(with:rect(x,y,w,h),options:[.usesLineFragmentOrigin,.usesFontLeading],attributes:[.font:font,.foregroundColor:color,.paragraphStyle:style])}
let starts=[0.0,6,17,27,38,45,54]
let titles=["01  서비스 진입","02  내 조건 선택","03  AI 기획 시작","04  기획 결과 생성","지도 · 굿즈 탐색","07  최종 검토","08  저장하고 활용"]
let captions=["홈에서 사용법을 확인한 뒤 ‘02 조건 선택’으로 이동하세요.","11개 필수 조건을 모두 입력·저장하세요. 모든 조건이 있어야 AI 기획을 시작할 수 있어요.","저장한 조건으로 추천 질문을 고치거나 직접 질문하세요. + 버튼으로 자료도 첨부할 수 있어요.","조건표·조사 내용·기획안·검토 항목을 확인하세요. 기획안 양식은 그대로 유지됩니다.","지도에서 운영 구역을 살펴보고 굿즈를 내 기획에 추가하세요.","미정 항목·자료 근거·예산·담당자를 확인한 뒤 검토 기록을 저장하세요.","PDF·Word·한글 파일로 저장하세요. 추가 질문과 조건 수정으로 다시 발전시킬 수 있어요."]
let url=URL(fileURLWithPath:out)
try? FileManager.default.removeItem(at:url)
let writer=try AVAssetWriter(outputURL:url,fileType:.mp4)
writer.shouldOptimizeForNetworkUse=true
let input=AVAssetWriterInput(mediaType:.video,outputSettings:[AVVideoCodecKey:AVVideoCodecType.h264,AVVideoWidthKey:W,AVVideoHeightKey:H,AVVideoCompressionPropertiesKey:[AVVideoAverageBitRateKey:1800000]])
input.expectsMediaDataInRealTime=false
let adaptor=AVAssetWriterInputPixelBufferAdaptor(assetWriterInput:input,sourcePixelBufferAttributes:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32ARGB,kCVPixelBufferWidthKey as String:W,kCVPixelBufferHeightKey as String:H])
writer.add(input);guard writer.startWriting() else {fatalError("Video writer: \(String(describing: writer.error))")};writer.startSession(atSourceTime:.zero)
for f in 0..<(60*fps){
 while !input.isReadyForMoreMediaData{Thread.sleep(forTimeInterval:0.005)}
 autoreleasepool {
 let time=Double(f)/Double(fps);let scene=starts.lastIndex(where:{$0<=time}) ?? 0
 var opt:CVPixelBuffer?;CVPixelBufferPoolCreatePixelBuffer(nil,adaptor.pixelBufferPool!,&opt)
 let pixel=opt!;CVPixelBufferLockBaseAddress(pixel,[])
 let ctx=CGContext(data:CVPixelBufferGetBaseAddress(pixel),width:W,height:H,bitsPerComponent:8,bytesPerRow:CVPixelBufferGetBytesPerRow(pixel),space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.noneSkipFirst.rawValue)!
 NSGraphicsContext.saveGraphicsState();NSGraphicsContext.current=NSGraphicsContext(cgContext:ctx,flipped:false)
 box(0,0,1280,720,light,0);box(24,20,1232,66,.white);text("대사투! FESTIVAL",48,36,430,27,purple,true);text("60초 사용 예시 · 안내용 가상 데이터",790,40,440,20,muted)
 let nav=["01 홈","02 조건 선택","03 AI 기획","04 기획 결과","05 축제 지도","06 굿즈","07 최종 검토","08 저장·활용"]
 for (i,n) in nav.enumerated(){let active=[0,1,2,3,4,6,7][scene]==i;box(Double(26+i*154),101,148,42,active ? purple:.white,9);text(n,Double(41+i*154),112,130,18,active ? .white:muted,true)}
 box(24,158,1232,436,.white);text(titles[scene],52,178,1100,29,purple,true)
 switch scene {
 case 0:
    text("지역의 이야기를, 함께 만드는 축제로.",85,262,1100,43,ink,true)
    text("조건 선택 → AI 기획 → 결과 → 최종 검토 → 저장",85,338,1100,27,muted)
    box(85,423,300,62,purple);text("조건 선택하기 →",110,440,280,27,.white,true)
    text("처음이라면 ‘사용법 먼저 알아보기’를 확인하세요.",430,440,740,24,muted)
 case 2:
    box(64,244,1120,72,light);text("추천 질문  ·  두류공원에서 가족이 즐길 여름 축제를 기획해줘",88,265,1080,27)
    if time>20 {box(270,332,914,77,purple);text("가족 관람객 500명, 예산 3천만 원으로 기획하고 싶어요.",298,354,870,26,.white)}
    if time>23 {box(64,428,975,77,light);text("대키미  ·  저장한 11개 조건으로 조사와 초안 작성을 이어갑니다.",88,449,930,25)}
    text("+  자료 첨부                 원하는 축제를 직접 적어 보세요.          보내기 →",75,541,1110,22,muted)
 case 1:
    let labels=["개최 연도   2027년","주최·주관   축제 기획팀","컨셉   참여형 체험","프로그램   사투리 퀴즈","규모   소규모 · 500명","테마   지역문화","기간   8월 27~29일","장소   두류공원","예산   3천만 원","대상   가족 관람객","목표   지역문화 체험 확대"]
    for (i,label) in labels.enumerated(){let x=Double(62+(i%2)*575),y=Double(234+(i/2)*48);box(x,y,550,42,light,10);text(label,x+18,y+10,520,20)}
    box(692,536,490,40,purple);text("필수 11/11개 저장하고 AI 기획 시작 →",711,546,465,20,.white,true)
 case 3:
    for (i,n) in ["조건표","조사 내용","기획안","검토 항목"].enumerated(){box(Double(63+i*286),240,267,48,i==2 ? purple:light,9);text(n,Double(86+i*286),253,240,23,i==2 ? .white:ink,true)}
    text("대사투! 가족 체험 축제  /  기획안 예시",70,320,1050,31,ink,true)
    text("1. 축제 개요   2. 목적·차별화   3. 프로그램   4. 추진 계획\n5. 사업비 계획   6. 안전관리   7. 기대효과   8. 신청 단체",70,379,1110,25,muted,false,110)
    box(70,499,1106,58,light);text("8개 항목의 양식은 고정 · 컨셉과 요청에 맞춰 내용을 수정합니다.",91,517,1070,24,purple)
 case 4:
    box(64,245,550,300,light);box(643,245,550,300,light)
    text("축제 지도",93,265,490,28,purple,true);text("구역을 눌러 운영 내용 확인",670,265,480,26,purple,true)
    for i in 0..<3 {box(Double(92+i*168),334,144,128,[purple,muted,purple][i]);text(["무대","체험","쉼터"][i],Double(113+i*168),382,120,24,.white,true)}
    text("굿즈 · 예시",670,334,470,27,ink,true);text("선택한 상품을 기획에 추가\n→ 필요하면 조건을 바꿔 재생성",670,388,490,24,muted,false,100)
 case 5:
    for (i,n) in ["미정 항목과 추가 조사할 내용 확인","자료의 원문·첨부 근거 확인","총 예산과 산출 근거 확인","담당자와 검토 의견 입력"].enumerated(){text((time>Double(46+i*2) ? "☑":"□")+"  "+n,76,Double(248+i*65),1120,28,i==3 ? purple:ink)}
    text("검토 기록 저장 → 내용이 바뀌면 다시 확인",76,527,1100,23,muted)
 default:
    text("내 기획안 저장 · 활용",76,258,1080,38,ink,true)
    for (i,n) in ["PDF 다운로드","Word 다운로드","한글(HWPX) 다운로드"].enumerated(){box(Double(76+i*372),338,346,70,purple);text(n,Double(95+i*372),361,325,24,.white,true)}
    text("추가 질문 또는 조건 수정 → 다시 생성 → 최종 검토",76,460,1100,29,purple,true)
    text("이 영상은 이용 방법을 보여주는 예시이며 실제 AI 결과는 입력에 따라 달라집니다.",76,524,1110,20,muted)
 }
 box(24,612,1232,88,purple);text(captions[scene],47,631,1180,26,.white,true,63)
 box(0,712,Double(W)*time/60,8,purple,0)
 // Animated pointer draws attention to the primary action, with a pulsing halo.
 let px=scene==0 ? 325.0 : scene==2 ? 1120.0 : 1174.0
 let py=scene==0 ? 468.0 : scene==2 ? 542.0 : 571.0
 purple.withAlphaComponent(0.14+0.10*sin(time*3)).setFill();NSBezierPath(ovalIn:rect(px-18,py-18,36,36)).fill()
 NSGraphicsContext.restoreGraphicsState()
 if f==0,let cg=ctx.makeImage(){let rep=NSBitmapImageRep(cgImage:cg);try? rep.representation(using:.png,properties:[:])?.write(to:URL(fileURLWithPath:out.replacingOccurrences(of:".mp4",with:"-poster.png")))}
 adaptor.append(pixel,withPresentationTime:CMTime(value:Int64(f),timescale:Int32(fps)));CVPixelBufferUnlockBaseAddress(pixel,[])
 }
}
input.markAsFinished();writer.endSession(atSourceTime:CMTime(seconds:60,preferredTimescale:600))
let sem=DispatchSemaphore(value:0);writer.finishWriting{sem.signal()};sem.wait()
if let error=writer.error{fatalError(error.localizedDescription)}
print("Created 60s tutorial:",out)
