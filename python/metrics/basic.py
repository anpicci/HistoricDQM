class BaseMetric:
    "baseclass for all metrics. should not be used on its own"
    def __init__(self):
        self._reference = None
        self._histo1 = None
        self._histo2 = None
        self._run = 0
        self._threshold = 1

    def setCache(self, cache):
        self.__cache = cache
    def setReference(self, histo): 
        self._reference = histo
    def setOptionalHisto1(self, histo): 
        self._histo1 = histo
    def setOptionalHisto2(self, histo): 
        self._histo2 = histo
    def setThreshold(self, threshold): 
        self._threshold = threshold
    def setCacheLocation(self, serverUrl, runNr, dataset, histoPath):
         self.__cacheLocation = (serverUrl, runNr, dataset, histoPath)
    def setRun(self, runNr):
        self._run = runNr

    def __call__(self, histo, cacheLocation=None):
        if not cacheLocation == None and not self.__cache == None and cacheLocation in self.__cache:
            result, entries = self.__cache[cacheLocation]
        else:
            assert (not histo==None), "reading from cache failed but no histo givento compute metric!"
            result = (0,0)
            try:
                result = self.calculate(histo)
            except StandardError as msg :
                print("Warning: fit failed, returning 0")
                print(msg)

            entries = histo.GetEntries()
            if not self.__cache == None:
                self.__cache[cacheLocation] = (result, entries)
        if entries < self._threshold:
            raise StandardError(" Number of entries (%s) is below threshold (%s) using '%s'"%(entries, self._threshold, self.__class__.__name__)) #, histo.GetName())
            #print(" Number of entries (%s) is below threshold (%s) using '%s'"%(entries, self._threshold, self.__class__.__name__))
        if not len(result) == 2:
            raise StandardError("calculate needs to return a tuple with the value and the error of the metric!")
        if not "__iter__" in dir(result[1]):
            result = (result[0], (result[1],result[1]))
        else:
            if not len(result[1]) == 2:
                raise StandardError("when you use assymmetric errors you need to specify exactly two values. You gave: '%s'"%result[1])

        return result

    def calculate(self, histo):
        raise StandardError("you should not use the baseclass as a metric. Use the derived classes!")
        
        
class SummaryMapPartition(BaseMetric):
    def __init__(self,  binx, nbinsy):
        self.__binx = binx
        self.__nbinsy = nbinsy

    def calculate(self, histo):
        value = 0
        for ybin in range(self.__nbinsy):
            ybin=ybin+1
            value += histo.GetBinContent(self.__binx , ybin)
            value1=value
        value /= self.__nbinsy
        return (value, 0)

class AverageYwithXCut(BaseMetric):
    def __init__(self,  nbinx):
        self.__nbinsx = nbinx

    def calculate(self, histo):
        value = 0
        Nbins = histo.GetNbinsX()
        self.__nbinsx=Nbins
        for xbin in range(self.__nbinsx):
            if histo.GetBinContent(xbin)>0:
                NN=xbin
        self.__nbinsx=NN-3
        for xbin in range(self.__nbinsx):
            value += histo.GetBinContent(xbin)
            value1=value
        value /= self.__nbinsx
        return (value, 0)


class Mean(BaseMetric):
    def calculate(self, histo):
        return (histo.GetMean(), histo.GetMeanError())

class MeanEntries(BaseMetric):
    def calculate(self, histo):
        return (histo.GetMean()*histo.GetEntries(), histo.GetMeanError()*histo.GetEntries())

class PixelEfficiency(BaseMetric):
    def calculate(self, histo):
        from math import sqrt
        num= histo.GetMean()*histo.GetEntries()
        den= histo.GetMean()*histo.GetEntries()+self._histo1.GetMean()*self._histo1.GetEntries()
        if den == 0:
            res= 0
            eres=0
        else:
            res=num/den
            eres=sqrt(res*(1-res)/den)
        return (res,eres)

class PixelDigiPerClusterPix(BaseMetric):
    def calculate(self, histo):
        from math import sqrt
        if "2" in histo.ClassName():
            num= histo.GetMean(3)
            den= self._histo1.GetMean(3)*self._histo2.GetMean(3)
        else:
            num= histo.GetMean()
            den= self._histo1.GetMean()*self._histo2.GetMean()
        if den == 0:
            res= 0
            eres=0
        else:
            res=num/den
            enum=histo.GetMeanError()
            eden=sqrt(self._histo1.GetMeanError()*self._histo1.GetMeanError()+self._histo2.GetMeanError()*self._histo2.GetMeanError())
            if num == 0:
                eres=0
            else:
                eres=res*sqrt((enum*enum)/(num*num)+(eden*eden)/(den*den))
        if num < 1:
            res=0
            eres=0
        return (res,eres)


class MeanRMS(BaseMetric):
    def calculate(self, histo):
        #print('mean:',histo.GetMean(), histo.GetMeanError())
        return (histo.GetMean(), histo.GetRMS())


class MeanY(BaseMetric):
    def calculate(self, histo):
        sumw     = histo.GetSumOfWeights()
        nentries = histo.GetEntries()
        return (sumw/nentries if nentries else 0, 0) 

class MeanYAxis(BaseMetric):
    def calculate(self, histo):
        return (histo.GetMean(2), histo.GetMeanError(2)) 

class MeanZAxis(BaseMetric):
    def calculate(self, histo):
        return (histo.GetMean(3), histo.GetMeanError(3)) 

class RMSXAxis(BaseMetric):
    def calculate(self, histo):
        return (histo.GetRMS(1), histo.GetRMSError(1)) 

class RMSYAxis(BaseMetric):
    def calculate(self, histo):
        return (histo.GetRMS(2), histo.GetRMSError(2)) 

class ProfileMean(BaseMetric):
    def calculate(self, histo):
        from math import sqrt
        nbinx=histo.GetNbinsX();
        nbiny=histo.GetNbinsY();
        summy=0
        sumSquare=0
        count=0
        for i in range(1,nbinx+1):
            for j in range(1,nbiny+1):
                if histo.GetBinContent(i,j) != 0 :
                    summy+=histo.GetBinContent(i,j)
                    sumSquare+=histo.GetBinContent(i,j)*histo.GetBinContent(i,j)
                    count+=1
        if count==0:
            return (0,0)
        rms= sqrt( sumSquare/count-(summy*summy/(count*count)) )
        return (summy/count, rms/sqrt(count))

class ProfileMeanBPixModules(BaseMetric):
    def __init__(self, modNum):
        self.__modCounter = 4-modNum

    def calculate(self, histo):
        from math import sqrt
        nbinx=histo.GetNbinsX();
        nbiny=histo.GetNbinsY();
        summy=0
        sumSquare=0
        count=0
        for j in range(1,nbiny+1):
            if histo.GetBinContent(1+self.__modCounter,j) != 0 :
                summy+=histo.GetBinContent(1+self.__modCounter,j)
                sumSquare+=histo.GetBinContent(1+self.__modCounter,j)*histo.GetBinContent(1+self.__modCounter,j)
                count+=1
            if histo.GetBinContent(nbinx-self.__modCounter,j) != 0 :
                summy+=histo.GetBinContent(nbinx-self.__modCounter,j)
                sumSquare+=histo.GetBinContent(nbinx-self.__modCounter,j)*histo.GetBinContent(nbinx-self.__modCounter,j)
                count+=1
        print(count)
        if count==0:
            return (0,0)
        rms= sqrt( sumSquare/count-(summy*summy/(count*count)) )
        return (summy/count, rms/sqrt(count))




#class WeightedMeanY(BaseMetric):
#    def calculate(self, histo):

class MeanDiff(BaseMetric):
    def calculate(self, histo):
        from math import sqrt
        return (histo.GetMean() - self._reference.GetMean(), 
                sqrt(histo.GetMeanError()**2 + self._reference.GetMeanError()**2))    

class Count(BaseMetric):
    def calculate(self, histo):
        return ( histo.GetEntries(), 0)

class MaxBin(BaseMetric):
    def calculate(self, histo):
        bin = histo.GetMaximumBin()
        return ( histo.GetBinCenter(bin), 0) 

class MaxExcursion(BaseMetric):
    def calculate(self, histo):
        from math import sqrt
        bmax = histo.GetMaximumBin()
        bmin = histo.GetMinimumBin()
        res=histo.GetBinContent(bmax)-histo.GetBinContent(bmin)
        err=sqrt(histo.GetBinError(bmax)*histo.GetBinError(bmax)+histo.GetBinError(bmin)*histo.GetBinError(bmin))
        return ( res, err) 

class BinCount(BaseMetric):
    def __init__(self,  name, noError = False):
        self.__name = name
        self.__noError = noError

    def calculate(self, histo):
        from math import sqrt
        binNr = self.__name
        if type(self.__name) == type(""):
            binNr = histo.GetXaxis().FindBin(self.__name)
        error = 0
        if not self.__noError:
            error = sqrt(histo.GetBinContent(binNr))
        return ( histo.GetBinContent(binNr), error)

class ROCfraction(BaseMetric):
    def __init__(self,  name, tot,noError = False):
        self.__name = name
        self.__tot = tot
        self.__noError = noError

    def calculate(self, histo):
        from math import sqrt
        binNr = self.__name
        if type(self.__name) == type(""):
            binNr = histo.GetXaxis().FindBin(self.__name)
        error = 0
        if not self.__noError:
            error = 100*sqrt(histo.GetBinContent(binNr))/self.__tot
        return ( 100*histo.GetBinContent(binNr)/self.__tot, error)

class FED25ErrorFraction(BaseMetric):
    def __init__(self, thr, norm, normErr=True):
        self.__thr = thr
        self.__norm = norm
        self.__normErr = normErr

    def calculate(self,histo):
        from math import sqrt
        ref=histo.GetMaximum()*self.__thr
        nbinx=histo.GetNbinsX();
        nbiny=histo.GetNbinsY();
        count=0
        for i in range(1,nbinx+1):
            for j in range(1,nbiny+1):
                if histo.GetBinContent(i,j)>ref:
                    count+=1
        res=float(count)/self.__norm
        err=0
        if self.__normErr :
            err=sqrt(res*(1-res)/(nbinx*nbiny))
        return (100*res, 100*err)

class StripFEDErrorFraction(BaseMetric):
    def __init__(self, fedId, errorType):
        self.__fedId = fedId
        self.__type = errorType

    def calculate(self,histo):
        from math import sqrt
        den=self._histo1.GetMaximum()
        num=histo.GetBinContent(self.__fedId+1-50,self.__type)
        if den==0:
            res=0
            err=0
        else:
            res=num/den
            err=sqrt(res*(1-res)/den)
        return (100*res, 100*err)



class StripBadComponent(BaseMetric):
    def __init__(self,  binsx, biny, norm):
        self.__binsx = binsx
        self.__biny = biny
        self.__norm = norm

    def calculate(self, histo):
        from math import sqrt
        num=0
        for bin in self.__binsx:
            num += histo.GetBinContent(bin,self.__biny)
        error = 0
        return ( 100*num/self.__norm, error)


class EntriesCount(BaseMetric):
    def __init__(self, startValue):
        self.__loVal = startValue

    def calculate(self, histo):
        from math import sqrt
        sum=float(0.0)
        for bin in range(histo.FindBin(self.__loVal),histo.GetNbinsX()+1) :
            sum+=histo.GetBinContent(bin)
        return ( sum, sqrt(1/sum)*sum if sum else 0)   

class EntriesRate(BaseMetric):
    def __init__(self,  startValue):
        self.__loVal = startValue
        print(self.__loVal)

    def calculate(self, histo):
        from math import sqrt
        trksum=float(0.0)
        for bin in range(histo.FindBin(self.__loVal),histo.GetNbinsX()+1) :
            trksum+=histo.GetBinContent(bin)
        nLS=0
        for bin in range(1,self._histo1.GetNbinsX()+1) :
            if self._histo1.GetBinContent(bin) > 0 :
                nLS+=1
        if nLS :
            return (trksum/(nLS*23), sqrt(trksum)/(nLS*23))
        else :
            return (0,0)



class RecoFraction(BaseMetric):
    def __init__(self,  name, noError = False):
        self.__name = name
        self.__noError = noError

    def calculate(self, histo):
        from math import sqrt
        binNr = self.__name
        if type(self.__name) == type(""):
            binNr = histo.GetXaxis().FindBin(self.__name)
        enum = 0
        if not self.__noError:
            enum = sqrt(histo.GetBinContent(binNr))
        num=histo.GetBinContent(binNr)
        den=self._histo1.GetEntries();
        if den == 0:
            res=0
            eres=0
        else:
            res=num/den
            eres=enum/den
        return ( res, eres)


class BinsCount(BaseMetric):
    def __init__(self, startBin):
        self.__loBin = startBin

    def calculate(self, histo):
        from math import sqrt
        sum=float(0.0)
        for bin in range(self.__loBin,histo.GetNbinsX()+1) : sum+=histo.GetBinContent(bin)
        return ( sum, sqrt(1/sum)*sum if sum else 0)   

class NormBinCount(BaseMetric):
    def __init__(self,  name, norm = None):
        self.__name = name
        self.__norm = norm
        self.__iWeightHisto = 0

    def calculate(self, histo):        
        from ROOT import TGraphAsymmErrors
        frac = self.__getWeightOneHisto(histo, self.__name)
        total = self.__getWeightOneHisto( histo, self.__norm)

        if(frac.GetEntries() > total.GetEntries()):
            raise StandardError(" comparing '%s' to '%s' in '%s' makes no sense eff > 1!"%(self.__name, self.__norm, histo.GetName()))
        
        eff = TGraphAsymmErrors(1)
        eff.BayesDivide(frac, total)
        if eff.GetN() < 1: 
            raise StandardError("Efficiency cannot be calculated '%s' in '%s'"%(self.__name, histo.GetName()))
        return ( eff.GetY()[0], (eff.GetEYlow()[0],eff.GetEYhigh()[0]) )

    def __getWeightOneHisto(self, histo, name):
        """return histo with one bin filled with entries of weight on to match hist at name
        if name == None use integral of histo."""
        from ROOT import TH1D
        from math import sqrt
        result = TH1D( ("%s"%name) + "%s"%self.__iWeightHisto,
                       ("%s"%name) + "%s"%self.__iWeightHisto,1,0,1)
        self.__iWeightHisto+=1
        bin = histo.GetSumOfWeights()
        if not name == None:
            binNr = name
            if type(name) == type(""):
                binNr = histo.GetXaxis().FindBin(name)
            bin =  histo.GetBinContent(binNr)
        result.Sumw2()
        result.SetBinContent(1, bin )
        result.SetBinError(1, sqrt(bin))
        return result
    


class Ratio(BaseMetric):
    def __init__(self,  low, high):
        self.__low = low
        self.__high = high

    def calculate(self, histo):
        from math import sqrt
        s = histo.Integral(histo.FindBin( self.__low),
                           histo.FindBin( self.__high))
        T = histo.Integral()
        B = T-s
        return (  s / B if B else 0,
                  sqrt( s + s*s/B ) / B if s and B else 1/B if B else 0 )

class Ratio1(BaseMetric):
    def __init__(self,  low, high):
        self.__low = low
        self.__high = high

    def calculate(self, histo):
        from math import sqrt
        s = histo.Integral(histo.FindBin( self.__low),
                           histo.FindBin( self.__high))
        Nbins = histo.GetSize()
        T = histo.Integral(0,Nbins)
        B = T-s
        return (  B / s if s else 0,
                  sqrt( B + B*B/s ) / s if s and B else 1/s if s else 0 )

class Fraction(BaseMetric):
    def __init__(self, low, high):
        self.__low = low
        self.__high = high

    def calculate(self, histo):
        from math import sqrt
        s = histo.Integral(histo.FindBin( self.__low),
                           histo.FindBin( self.__high))
        T = histo.GetEntries()
        return ( s/T if T else 0,
                 sqrt( 1/s + 1/T )*(s/T) if s and T else 1/sqrt(T) if T else 0)

class Fraction1(BaseMetric): 
    def __init__(self, low, high):
        self.__low = low
        self.__high = high

    def calculate(self, histo):
        from math import sqrt
        s = histo.Integral(histo.FindBin( self.__low),
                           histo.FindBin( self.__high))
        print("AAA",self.__high,self.__high+1)
        Nbins = histo.GetSize()
#        T = histo.Integral(0,self.__high+1)
        T = histo.Integral(0,Nbins)
        B = T-s
        return ( B/T if T else 0,
                 sqrt( s*s*B + B*B*s ) / (T*T) if s and B else 1/T if T else 0)

    
class FractionInBin(BaseMetric):
    def __init__(self, bin):
        self.__bin = bin

    def calculate(self, histo):
        from math import sqrt
        s = histo.GetBinContent(self.__bin)
        T = histo.GetEntries()
        return ( s/T if T else 0,
                 sqrt(1/T + 1/s)*s/T if T else 0)
    
class FractionInBinArray(BaseMetric):
    def __init__(self, binsnum, binsden):
        self.__binsnum = binsnum
        self.__binsden = binsden
        
    def calculate(self, histo):
        from math import sqrt
        num=float(0.0)
        den=float(0.0)
        
        for bn in self.__binsnum : num+=histo.GetBinContent(bn)
        for bd in self.__binsden : den+=histo.GetBinContent(bd)
        return ( num/den if den else 0,
                 sqrt(1/num + 1/den)*num/den if den and num else 0)    

class MeanYRange(BaseMetric):
    def __init__(self, ymin, ymax):
        self.__ymin = float(ymin)
        self.__ymax = float(ymax)
        
    def calculate(self, histo):
        sum , count = 0 , 0
        for i in range(self.__ymin,self.__ymax):
            for j in range(0,histo.GetXaxis().GetNbins()+1):
                sum+=histo.GetBinContent(j,i)
                count+=1
        if count==0:
            return (0,0)
        return (sum/count,0)

class Mean2D(BaseMetric):
    def calculate(self,histo):
        sum, count = 0 , 0
        for i in range(histo.GetXaxis().GetNbins()):
            for j in range(histo.GetYaxis().GetNbins()):
                sum+=histo.GetBinContent(i,j)
                count+=1
        if count==0:
            return (0,0)
        return (sum/count, 0)

class BinRatio2D(BaseMetric):
    def __init__(self, Nxbin,Nybin,Dxbin,Dybin):
        self.__Nxbin = int(Nxbin)
        self.__Nybin = int(Nybin)
        self.__Dxbin = int(Dxbin)
        self.__Dybin = int(Dybin)

    def calculate(self,histo):
        from math import sqrt
        num=float(0.0)
        den=float(0.0)
        num=histo.GetBinContent(self.__Nxbin,self.__Nybin)
        den=histo.GetBinContent(self.__Dxbin,self.__Dybin)
        if den==0:
            return (0,0)
        else:
            res=num/den
        return (res, res*sqrt((1./den)+(1./num)))

class BinCount2D(BaseMetric):
    def __init__(self, xbin,ybin, normErr=True):
        self.__xbin = int(xbin)
        self.__ybin = int(ybin)
        self.__normErr = normErr

    def calculate(self,histo):
        from math import sqrt
        res=histo.GetBinContent(self.__xbin,self.__ybin)
        err=histo.GetBinError(self.__xbin,self.__ybin)
        if self.__normErr :
            err=err/sqrt(histo.GetEntries())
        return (res, err)

class Bin2DRatio(BaseMetric):
    def __init__(self, xbin,ybin, normEntries=True):
        self.__xbin = int(xbin)
        self.__ybin = int(ybin)
        self.__normE = normEntries

    def calculate(self,histo):
        from math import sqrt
        num=histo.GetBinContent(self.__xbin,self.__ybin)
        den=self._histo1.GetBinContent(self.__xbin,self.__ybin)
        if self.__normE :
            num=num*histo.GetEntries();
            den=den*self._histo1.GetEntries();
            err=sqrt(num)
        else:
            err=histo.GetBinError(self.__xbin,self.__ybin)/sqrt(histo.GetEntries())
        if den==0:
            res=0
            err=0
        else:
            res=num/den
            err=err/den
        return (res, err)



class MeanYForXBin(BaseMetric):
    def __init__(self, xbin):
        self.__xbin = int(xbin)

    def calculate(self,histo):
        sum,count = 0,0
        for i in range(1,histo.GetYaxis().GetNbins()+1):
            if histo.GetBinContent(self.__xbin,i) >= 0:
                sum+=histo.GetBinContent(self.__xbin,i)
            count+=1
        if count == 0:
            return (0,0)
        return (sum/count, 0)
        

class MeanPosOnly(BaseMetric):
    def calculate(self,histo):
        sum,count = 0,0
        for i in range(1,histo.GetXaxis().GetNbins()+1):
            if histo.GetBinContent(i,1) >= 0:
                sum += histo.GetBinContent(i,1)
            count+=1
        if count == 0:
            return(0,0)
        return (sum/count , 0)
    
class MeanXRange(BaseMetric):
    def __init__(self, xmin, xmax):
        self.__xmin = int(xmin)
        self.__xmax = int(xmax)
        
    def calculate(self, histo):
        sum,count = 0,0
        for i in range(self.__xmin,self.__xmax):
            for j in range(1,histo.GetYaxis().GetNbins()+1):
                if histo.GetBinContent(i,j) >= 0:
                    sum+=histo.GetBinContent(i,j)
                count+=1
        if count==0:
            return (0,0)
        return (sum/count,0)

class Quantile(BaseMetric):
    def __init__(self,  frac = 0.95):
        self.__frac = float(frac)
        from ROOT import gROOT
        gROOT.LoadMacro( 'Quantile.h+' )

    def calculate(self, histo):
        from ROOT import Quantile
        q = Quantile(histo)
        "frac is the fraction from the left"
        quant, quantErr = q.fromHead(self.__frac)
        if quantErr == 0.:
            raise StandardError(" Quantile cannot be calculated!")
        return (quant,quantErr)

#--- statistical Tests            
class Kolmogorov(BaseMetric):
    def calculate(self, histo):
        k = histo.KolmogorovTest( self._reference)
        return (k, 0)

class Chi2(BaseMetric):
    def calculate(self, histo):
        chi2 = histo.Chi2Test( self._reference, "UUNORMCHI2")
        return (chi2, 0 )

class NormChi2(BaseMetric):
    def calculate(self, histo):
        chi2 = histo.Chi2Test( self._reference, "UUNORMCHI2/NDF")
        return (chi2, 0 )
