import ROOT
import numpy
import ctypes 
import math

RDF = ROOT.RDataFrame.RDataFrame
colors = [ROOT.kMagenta, ROOT.kAzure-2, ROOT.kOrange-3, ROOT.kRed, ROOT.kCyan+4, ROOT.kViolet+5, ROOT.kYellow-6, ROOT.kTeal-7]

def PlotTheoryStop():
    f = open("inputs/GetRPVSTOP.txt", "r")
    X = []
    Y = []
    Yp = []
    Ym = []
    for x in f:
        m = float(x.split("_")[0])
        y = float(x.split("_")[2])
        e = float(x.split("_")[4])
        yp = y * (100. + e)/100.
        ym = y * (100. - e)/100.
        X.append(m)
        Y.append(y)
        Yp.append(yp)
        Ym.append(ym)
    G = ROOT.TGraph(len(X), numpy.array(X), numpy.array(Y))
    G.SetLineColor(ROOT.kBlack)
    G.SetLineWidth(2)
    G.SetLineStyle(10)
    Gu = ROOT.TGraph(len(X), numpy.array(X), numpy.array(Yp))
    Gd = ROOT.TGraph(len(X), numpy.array(X), numpy.array(Ym))
    for g in [Gu,Gd]:
        g.SetLineColor(ROOT.kBlack)
        g.SetLineStyle(3)
    return G, Gu, Gd

def Template_Replace(F, O, R):
	with open(F, 'r') as file :
		filedata = file.read()
	filedata = filedata.replace(O, R)
	with open(F, 'w') as file:
		file.write(filedata)

def RDFDeltaR(rdf, name, jet1, jet2):
    # ROOT.gInterpreter.ProcessLine("auto Use_Fit_"+newname+" = "+fit+";")
    usefit_code = 	'''
                    #include <TROOT.h>
                    float myDeltaR(float pt1, float pt2, float eta1, float eta2, float phi1, float phi2, float m1, float m2)
                    {
                        TLorentzVector j1 = TLorentzVector();
                        j1.SetPtEtaPhiM(pt1, eta1, phi1, m1);
                        TLorentzVector j2 = TLorentzVector();
                        j2.SetPtEtaPhiM(pt2, eta2, phi2, m2);
                        return j1.DeltaR(j2);
                    }
                    '''
    ROOT.gInterpreter.Declare(usefit_code)
    new_rdf = rdf.Define(name, "myDeltaR(j%d_pt, j%d_pt, j%d_eta, j%d_eta, j%d_phi, j%d_phi, j%d_m, j%d_m)" % (jet1,jet2,jet1,jet2,jet1,jet2,jet1,jet2))
    return new_rdf

def MakeNBinsFromMinToMax(N,Min,Max):
    BINS = []
    for i in range(N+1):
        BINS.append(Min+(i*(Max-Min)/N))
    return numpy.array(BINS)

def GoodPlotFormat(H, *args): # Handy little script for color/line/fill/point/etc...
	try: H.SetStats(0)
	except: print " ------------ [  No stats box found!  ]"
	if args[0] == 'thickline':
		H.SetLineColor(args[1])
		H.SetLineWidth(2)
	if args[0] == 'thinline':
		H.SetLineColor(args[1])
		H.SetLineWidth(1)
		H.SetLineStyle(args[2])
	if args[0] == 'fill':
		H.SetLineColor(args[1])
		H.SetFillColor(args[1])
		H.SetFillStyle(args[2])
	if args[0] == 'markers':
		H.SetLineColor(args[1])
		H.SetMarkerColor(args[1])
		H.SetMarkerStyle(args[2])
	H.GetXaxis().SetTitleSize(0.04)
	
def FindAndSetMax(*args):
	if len(args) == 1: args = args[0]
	maximum = 0.0
	for i in args:
		i.SetStats(0)
		t = i.GetMaximum()
		if t > maximum:
			maximum = t
	for j in args:
		j.GetYaxis().SetRangeUser(0,maximum*1.35)#should be 1.35 (below as well)
		j.SetLineWidth(2)
	return maximum*1.35

def GetM2jA(F, T, N, W, C, BR="evt_2JetM", BIN=MakeNBinsFromMinToMax(160, 0.0, 4000.0), XT="Average Dijet Mass [GeV]", YT="Events/GeV", divbin=True):
    if BR is None: BR="evt_2JetM"
    if BIN is None: BIN=MakeNBinsFromMinToMax(160, 0.0, 4000.0)
    if XT is None: XT="Average Dijet Mass [GeV]"
    if YT is None: YT="Events/GeV"
    Ch = ROOT.TChain(T)
    Ch.Add(F)
    rdf = RDF(Ch)
    rdf = rdf.Define("total_weight", W)
    rdf = rdf.Define("evt_alpha", "evt_2JetM/evt_4JetM")
    Rlazy = rdf.Filter(C).Histo1D(("tempH", ";%s;%s" % (XT, YT), len(BIN)-1, numpy.array(BIN)), BR,"total_weight")
    R = Rlazy.GetValue()
    if divbin:
        for n in range(1, R.GetNbinsX()+1):
            R.SetBinContent(n, R.GetBinContent(n)/R.GetBinWidth(n))
            R.SetBinError(n, R.GetBinError(n)/R.GetBinWidth(n))
    R.SetStats(0)
    return R.Clone(N)

def GetM2jM4j(F, T, N, W, C, BRX="evt_2JetM", BRY="evt_4JetM", BINX=MakeNBinsFromMinToMax(100, 100.0, 2000.0), BINY=MakeNBinsFromMinToMax(100, 100.0, 4000.0), XT="Average Dijet Mass [GeV]", YT="4-Jet Mass [GeV]"):
    Ch = ROOT.TChain(T)
    Ch.Add(F)
    rdf = RDF(Ch)
    rdf = rdf.Define("total_weight", W)
    rdf = rdf.Define("evt_alpha", "evt_2JetM/evt_4JetM")
    Rlazy = rdf.Filter(C).Histo2D(("tempH", ";%s;%s" % (XT, YT), len(BINX)-1, numpy.array(BINX), len(BINY)-1, numpy.array(BINY)), BRX, BRY,"total_weight")
    R = Rlazy.GetValue()
    R.SetStats(0)
    return R.Clone(N)

def AddCMSLumi(pad, fb=None, extra=None):
    cmsText     = "CMS" + (" " + str(extra) if extra is not None else "")
    cmsTextFont   = 61  
    lumiTextSize     = 0.45
    lumiTextOffset   = 0.15
    cmsTextSize      = 0.5
    cmsTextOffset    = 0.15
    H = pad.GetWh()
    W = pad.GetWw()
    l = pad.GetLeftMargin()
    t = pad.GetTopMargin()
    r = pad.GetRightMargin()
    b = pad.GetBottomMargin()
    e = 0.025
    pad.cd()
    lumiText = (str(fb)+" fb^{-1}" if fb is not None else "") + " (13 TeV)"
    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextAngle(0)
    latex.SetTextColor(ROOT.kBlack)	
    extraTextSize = 0.76*cmsTextSize
    latex.SetTextFont(42)
    latex.SetTextAlign(31) 
    latex.SetTextSize(lumiTextSize*t)	
    latex.DrawLatex(1-r,1-t+lumiTextOffset*t,lumiText)
    pad.cd()
    latex.SetTextFont(cmsTextFont)
    latex.SetTextSize(cmsTextSize*t)
    latex.SetTextAlign(11)
    latex.DrawLatex(l, 1-t+cmsTextOffset*t, cmsText)
    pad.Update()

def stylePull(Hin, Ein, name, fitResult=None, signals=None, title=None, xTitle=None, yTitle=None, CH=None, rangeX=None, rangeY=None, pullRangeY=None, displayCI=False, displaychisquare=False, legTitle=None, lumi=None, CMSExtra=None):
    # H = ROOT.TH1()
    # E = ROOT.TH1() or ROOT.TF1()
    # name = string
    xbins = []
    MinNonZeroBins = []
    MaxNonZeroBins = []
    for n in range(Hin.GetXaxis().GetNbins()+1): xbins.append(Hin.GetXaxis().GetBinUpEdge(n))

    H = Hin.Clone(Hin.GetName()+"_clone")
    E = Ein.Clone(Ein.GetName()+"_clone")

    SignalErr = []
    if signals is not None:
        for S in signals: SignalErr.append(S.Clone())

    C = ROOT.TCanvas()
    C.SetCanvasSize(1000, 1000)
    pad = ROOT.TPad(name, name, 0, 0.25, 1, 1)
    pad.SetTopMargin(0.1)
    pad.SetBottomMargin(0.005)
    pad.SetLeftMargin(0.13)
    pad.SetRightMargin(0.15)
    pad.SetLogy()

    legendx = 0.80
    if displayCI: legendx = legendx - 0.03
    if displaychisquare: legendx = legendx - 0.1
    if signals is not None:
        for n in signals: legendx = legendx - 0.04
    legend = ROOT.TLegend(0.55, legendx, 0.84, 0.88)
    if legTitle is not None: legend.SetHeader(legTitle)
    legend.SetFillColor(0)
    legend.SetLineColor(0)

    for n in range(1, H.GetXaxis().GetNbins()+1):
        try:
            if H.GetBinError(n) == 0 and H.GetXaxis().GetBinUpEdge(n) <= E.GetHistogram().GetBinLowEdge(E.GetHistogram().FindFirstBinAbove(0)): H.SetBinError(n, 0)
        except:
            if H.GetXaxis().GetBinUpEdge(n) <= E.GetBinLowEdge(E.FindFirstBinAbove(0)): H.SetBinError(n, 0)
    H.SetLineColor(ROOT.kBlack)
    if yTitle is not None: H.GetYaxis().SetTitle(yTitle)
    H.SetMarkerStyle(20)
    H.SetMarkerSize(0.9)
    H.SetLineWidth(1)
    H.SetStats(0)
    if title is not None: H.SetTitle(title)
    E.SetLineWidth(1)
    pad.cd()
    H.Draw()
    E.SetLineColor(ROOT.kGreen+3)
    E.SetFillColor(ROOT.kGreen-9)
    E.SetFillStyle(1001)
    E.Draw("same hist")
    try: MinNonZeroBins.append(H.FindFirstBinAbove(0)-5)
    except: MinNonZeroBins.append(H.FindFirstBinAbove(0))
    MaxNonZeroBins.append(H.FindLastBinAbove(0)+5)

    # bins = []
    # for n in range(H.GetNbinsX()): bins.append(H.GetXaxis().GetBinUpEdge(n))
    # binsH = ROOT.TH1F("binsH","",len(bins)-1,numpy.array(bins))
    # for i in range(1,len(bins)+1):
    #     binsH.SetBinContent(i,binsH.GetXaxis().GetBinWidth(i))
    #     binsH.SetBinError(i,0)
    CI = Hin.Clone("CI_"+name)
    CIG = ROOT.TGraphErrors()
    CIpull = ROOT.TH1F()
    if displayCI:
        # confidence intervals
        if CH is None:
            CIG = ROOT.TGraphErrors(H)
            CIG.SetName("CI_"+name+"_graph")
            for i in range(CIG.GetN()): CIG.SetPoint(i, CIG.GetX()[i], 0)
            ROOT.TVirtualFitter.GetFitter().GetConfidenceIntervals(CIG)
            x, y, n = ctypes.c_double(), ctypes.c_double(), 0
            for m in range(CIG.GetN()):
                CIG.GetPoint(m, x, y)
                n = CI.FindBin(x.value)
                CI.SetBinContent(n, y.value if not math.isnan(y.value) else 0)
                CI.SetBinError(n, CIG.GetErrorY(m) if not math.isnan(CIG.GetErrorY(m)) else 0)
            CI.SetFillStyle(3244)
            CI.SetFillColorAlpha(ROOT.kGreen-2, 0.8)
            CI.SetLineColor(ROOT.kGreen-2)
        else:
            CI = CH
            CI.SetFillStyle(3244)
            CI.SetFillColorAlpha(ROOT.kGreen-2, 0.8)
            CI.SetLineColor(ROOT.kGreen-2)

        for n in range(1, CI.GetNbinsX()+1):
            try:
                if CI.GetXaxis().GetBinUpEdge(n) <= E.GetHistogram().GetBinLowEdge(E.GetHistogram().FindFirstBinAbove(0)) or CI.GetXaxis().GetBinUpEdge(n) >= E.GetHistogram().GetBinLowEdge(E.GetHistogram().FindLastBinAbove(0)):
                    CI.SetBinContent(n, 0)
                    CI.SetBinError(n, 0)
            except:
                if CI.GetXaxis().GetBinUpEdge(n) <= E.GetBinLowEdge(E.FindFirstBinAbove(0)) or CI.GetXaxis().GetBinUpEdge(n) >= E.GetBinLowEdge(E.FindLastBinAbove(0)):
                    CI.SetBinContent(n, 0)
                    CI.SetBinError(n, 0)
        CI.Draw("same e2")

        # confidence interval pulls
        CIpull = Hin.Clone("CIpull_"+name)
        for n in range(1, CIpull.GetNbinsX()+1):
            err = 1.4
            if H.GetBinContent(n) != 0: err = H.GetBinError(n)
            CIpull.SetBinContent(n, 0)
            CIpull.SetBinError(n, CI.GetBinError(n)/err)
        for n in range(1, CIpull.GetNbinsX()+1):
            try:
                if CIpull.GetXaxis().GetBinUpEdge(n) <= E.GetHistogram().GetBinLowEdge(E.GetHistogram().FindFirstBinAbove(0)) or CIpull.GetXaxis().GetBinUpEdge(n) >= E.GetHistogram().GetBinLowEdge(E.GetHistogram().FindLastBinAbove(0)):
                    CIpull.SetBinContent(n, 0)
                    CIpull.SetBinError(n, 0)
            except:
                if CIpull.GetXaxis().GetBinUpEdge(n) <= E.GetBinLowEdge(E.FindFirstBinAbove(0)) or CIpull.GetXaxis().GetBinUpEdge(n) >= E.GetBinLowEdge(E.FindLastBinAbove(0)):
                    CIpull.SetBinContent(n, 0)
                    CIpull.SetBinError(n, 0)
        CIpull.SetFillStyle(3244)
        CIpull.SetFillColorAlpha(ROOT.kGreen-2, 0.8)
        CIpull.SetLineColor(ROOT.kGreen-2)

    legend.AddEntry(H, Hin.GetName())
    legend.AddEntry(E, Ein.GetName(), "f")
    if displaychisquare is True:
        chisquare = E.GetChisquare()
        ndof = E.GetNDF()
        csn = chisquare/ndof
        fpr = E.GetProb()
        o = ROOT.TH1F()
        o.SetMarkerStyle(0)
        o.SetMarkerColor(ROOT.kWhite)
        o.SetLineColor(ROOT.kWhite)
        legend.AddEntry(o, "#chi^{2} = %.2f" % chisquare)
        legend.AddEntry(o, "ndof = %d" % ndof)
        legend.AddEntry(o, "#chi^{2}/ndof = %.2f" % csn)
        legend.AddEntry(o, "Fit Probability = %.2f" % fpr)
    if displayCI: legend.AddEntry(CI, "Uncertainty", "f")

    if signals is not None:
        for n in range(len(signals)):
            for x in range(1, signals[n].GetNbinsX()):
                errs = 1.4
                if H.GetBinContent(x) != 0: errs = H.GetBinError(x)
                SignalErr[n].SetBinContent(x, signals[n].GetBinContent(x)/err)
                SignalErr[n].SetBinError(x, 0)
                signals[n].SetBinError(x, 0)
            signals[n].SetMarkerColor(colors[n])
            signals[n].SetFillColor(ROOT.kWhite)
            signals[n].SetFillStyle(1001)
            signals[n].SetLineWidth(1)
            signals[n].SetLineColor(colors[n])
            signals[n].Draw("hist same")
            # SignalErr[n].SetMarkerColor(colors[n])
            # SignalErr[n].SetLineWidth(1)
            # SignalErr[n].SetLineColor(colors[n])
            # try:
            #     if signals[n].GetXaxis().GetBinUpEdge(n) <= E.GetHistogram().GetBinLowEdge(E.GetHistogram().FindFirstBinAbove(0)):
            #         SignalErr[n].SetBinContent(n, 0)
            #         signals[n].SetBinContent(n, 0)
            #         SignalErr[n].SetBinError(n, 0)
            # except:
            #     if signals[n].GetXaxis().GetBinUpEdge(n) <= E.GetBinLowEdge(E.FindFirstBinAbove(0)):
            #         SignalErr[n].SetBinContent(n, 0)
            #         signals[n].SetBinContent(n, 0)
            #         SignalErr[n].SetBinError(n, 0)
            legend.AddEntry(signals[n], signals[n].GetName(), "f")
            try: MinNonZeroBins.append(signals[n].FindFirstBinAbove(0)-5)
            except: MinNonZeroBins.append(signals[n].FindFirstBinAbove(0))
            MaxNonZeroBins.append(signals[n].FindLastBinAbove(0)+5)

    if rangeX is not None: H.GetXaxis().SetRangeUser(rangeX[0], rangeX[1])
    else: H.GetXaxis().SetRangeUser(min(MinNonZeroBins), max(MaxNonZeroBins))
    
    if rangeY is not None: H.GetYaxis().SetRangeUser(rangeY[0], rangeY[1])
    H.Draw("same")
    legend.Draw("same")
    pull = H.Clone("p_"+name)
    pull.Add(E, -1)
    for n in range(1, pull.GetXaxis().GetNbins()):
        pull.SetBinError(n, 1.)
        try:
            if pull.GetXaxis().GetBinUpEdge(n) <= E.GetHistogram().GetBinLowEdge(E.GetHistogram().FindFirstBinAbove(0)):
                pull.SetBinContent(n, 0)
                pull.SetBinError(n, 0)
            else:
                if H.GetBinError(n) != 0: pull.SetBinContent(n, pull.GetBinContent(n)/H.GetBinError(n))
                else: pull.SetBinContent(n, pull.GetBinContent(n)/1.4)
        except:
            if pull.GetXaxis().GetBinUpEdge(n) <= E.GetBinLowEdge(E.FindFirstBinAbove(0)):
                pull.SetBinContent(n, 0)
                pull.SetBinError(n, 0)
            else:
                if H.GetBinError(n) != 0: pull.SetBinContent(n, pull.GetBinContent(n)/H.GetBinError(n))
                else: pull.SetBinContent(n, pull.GetBinContent(n)/1.4)
        if H.GetBinContent(n) == 0:
            pull.SetBinContent(n, 0)
            pull.SetBinError(n, 0)

    pullpad = ROOT.TPad("pp_"+name, '', 0, 0, 1, 0.25)
    pullpad.SetLeftMargin(0.13)
    pullpad.SetRightMargin(0.15)
    pullpad.SetTopMargin(0.04)
    pullpad.SetBottomMargin(0.3)
    pullpad.SetGrid()
    pull.SetBit(ROOT.TH1.kNoTitle)
    pull.SetStats(0)
    pull.SetMarkerStyle(20)
    pull.SetMarkerColor(ROOT.kBlack)
    pull.SetMarkerSize(0.9)
    pull.SetLineWidth(1)
    pull.GetXaxis().SetLabelSize(0.1)
    if xTitle is not None: pull.GetXaxis().SetTitle(xTitle)
    pull.GetXaxis().SetTitleSize(0.1)
    pull.GetYaxis().SetNdivisions(505)
    pull.GetYaxis().SetLabelSize(0.1)
    pull.GetYaxis().SetTitle("#frac{Data - Fit}{Uncertainty}")
    pull.GetYaxis().SetTitleSize(0.08)
    pull.GetYaxis().SetTitleOffset(0.5)
    pull.GetYaxis().CenterTitle()
    pull.SetMarkerStyle(20)
    # indicator = ROOT.TF1('ind_'+name, '0', min(MinNonZeroBins), max(MaxNonZeroBins))
    indicator = pull.Clone("ind_"+name)
    indicator.Add(pull, -1)
    indicator.SetLineColor(ROOT.kBlack)
    indicator.SetLineWidth(1)

    pullpad.cd()
    if rangeX is not None: pull.GetXaxis().SetRangeUser(rangeX[0], rangeX[1])
    else: pull.GetXaxis().SetRangeUser(min(MinNonZeroBins), max(MaxNonZeroBins))
    indicator.Draw("hist")
    if displayCI: CIpull.Draw("same e2")
    # if signals is not None:
    #     for n in range(len(signals)): SignalErr[n].Draw("same hist")
    pull.Draw("same")
    maxpull = max(abs(pull.GetMaximum()),abs(pull.GetMinimum()))
    if pullRangeY is not None: indicator.GetYaxis().SetRangeUser(pullRangeY[0], pullRangeY[1])
    else: pull.GetYaxis().SetRangeUser(-maxpull - 0.2, maxpull + 0.2) # asymmetric pulls

    AddCMSLumi(pad, lumi, CMSExtra)

    C.cd()
    pad.Draw()
    pullpad.Draw()
    C.Print(name + ".png")
    C.Close()
    ROOT.gSystem.ProcessEvents()