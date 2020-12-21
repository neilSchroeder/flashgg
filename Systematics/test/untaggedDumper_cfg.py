import FWCore.ParameterSet.Config as cms
import FWCore.Utilities.FileUtils as FileUtils
import FWCore.ParameterSet.VarParsing as VarParsing
from flashgg.Systematics.SystematicDumperDefaultVariables import minimalVariables,minimalHistograms,minimalNonSignalVariables,systematicVariables
from flashgg.Systematics.SystematicDumperDefaultVariables import minimalVariablesHTXS,systematicVariablesHTXS
import os
import copy
from flashgg.MetaData.MetaConditionsReader import *

# ========================================================================
# Standard configuration setting
process = cms.Process("FLASHggSyst")
process.load("FWCore.MessageService.MessageLogger_cfi")
process.load("Configuration.StandardSequences.GeometryDB_cff")
process.load("Configuration.StandardSequences.MagneticField_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_condDBv2_cff")
process.maxEvents   = cms.untracked.PSet( input  = cms.untracked.int32( 10 ) )
process.options     = cms.untracked.PSet( wantSummary = cms.untracked.bool(True) )
process.MessageLogger.cerr.FwkReport.reportEvery = cms.untracked.int32( 1000 )

process.source = cms.Source ("PoolSource",
                             fileNames = cms.untracked.vstring(
'file:/eos/cms/store/user/youying/forTutorial/myMicroAODOutputFile_numEvent1000.root'
                             )
)

process.TFileService = cms.Service("TFileService",
                                   fileName = cms.string("test.root"))


from flashgg.MetaData.JobConfig import customize

customize.options.register('ignoreNegR9',
                           True,
                           VarParsing.VarParsing.multiplicity.singleton,
                           VarParsing.VarParsing.varType.bool,
                           'ignoreNegR9'
                           )

# set default options if needed
customize.setDefault("maxEvents",300)
customize.setDefault("targetLumi",1.00e+3)
customize.parse()
customize.metaConditions = MetaConditionsReader(customize.metaConditions)

# =============================================================================================
### Global Tag
from Configuration.AlCa.GlobalTag import GlobalTag
if customize.processId == "Data": process.GlobalTag.globaltag = str(customize.metaConditions['globalTags']['data'])
else: process.GlobalTag.globaltag = str(customize.metaConditions['globalTags']['MC'])

# =============================================================================================
### Untagged 

from flashgg.Systematics.SystematicsCustomize import *

process.load("flashgg/Taggers/flashggTagSequence_cfi")
import flashgg.Taggers.flashggTagSequence_cfi as tagSequence
process.flashggTagSequence = tagSequence.flashggPrepareTagSequence(process,customize.metaConditions)

process.flashggTagSequence.remove(process.flashggWHLeptonicTag)

process.flashggTHQLeptonicTag.processId = cms.string(str(customize.processId))

print process.flashggTagSequence

# ===============================================================================================
#systematics
process.load('flashgg.Systematics.flashggDiPhotonSystematics_cfi')
import flashgg.Systematics.flashggDiPhotonSystematics_cfi as diPhotons_syst
diPhotons_syst.setupDiPhotonSystematics( process, customize )
process.flashggPreselectedDiPhotons.src = cms.InputTag('flashggDiPhotonSystematics')

useEGMTools(process)
signal_processes = ["ggh_","vbf_","wzh_","wh_","zh_","bbh_","thq_","thw_","tth_","ggzh_","HHTo2B2G","GluGluHToGG","VBFHToGG","VHToGG","ttHToGG","Acceptance","hh","vbfhh","qqh","ggh","tth","vh"]
is_signal = reduce(lambda y,z: y or z, map(lambda x: customize.processId.count(x), signal_processes))

applyL1Prefiring = customizeForL1Prefiring(process, customize.metaConditions, customize.processId)

# ===============================================================================================
### Set Diphoton Producer
process.load("flashgg.Taggers.flashggUpdatedIdMVADiPhotons_cfi")

# ===============================================================================================
### Untagged Dumper setting

from flashgg.Taggers.tagsDumpers_cfi import createTagDumper
process.diphotonDumper = createTagDumper("UntaggedTag")
process.diphotonDumper.src = "flashggUntagged"
process.diphotonDumper.dumpTrees = True
process.diphotonDumper.dumpWorkspace = False
process.diphotonDumper.quietRooFit = True

#uprocess.load('flashgg.Taggers.diphotonDumper_cfi')
#process.diphotonDumper.className = "CutBasedDiPhotonDumper"
#process.diphotonDumper.src = "flashggUntagged"
#process.diphotonDumper.dumpTrees = True
#process.diphotonDumper.dumpWorkspace = False
#process.diphotonDumper.quietRooFit = True

process.diphotonDumper.nameTemplate ="$PROCESS_$SQRTS_$LABEL_$SUBCAT"

# ===============================================================================================

# Set variables in N-tuples
untagged_variables = [
        "CMS_hgg_mass[320,100,180]:=diPhoton.mass",
        "leadPt                   :=leadingPhoton.pt",
        "subleadPt                :=subLeadingPhoton.pt",
        "leadEta                  :=leadingPhoton.eta",
        "subleadEta               :=subLeadingPhoton.eta",
        "leadSCEta                :=leadingPhoton.superCluster.eta",
        "subleadSCEta             :=subLeadingPhoton.superCluster.eta",
        "leadPhi                  :=leadingPhoton.phi",
        "subleadPhi               :=subLeadingPhoton.phi",
        "leadEnergy               :=leadingPhoton.energy",
        "subleadEnergy            :=subLeadingPhoton.energy",
        "minR9                    :=min(leadingPhoton.full5x5_r9,subLeadingPhoton.full5x5_r9)",
        "maxEta                   :=max(abs(leadingPhoton.superCluster.eta),abs(leadingPhoton.superCluster.eta))",
        "lead_R9                  :=leadingPhoton.full5x5_r9",
        "sublead_R9               :=subLeadingPhoton.full5x5_r9",
        "lead_S4                  :=leadingPhoton.s4",
        "sublead_S4               :=subLeadingPhoton.s4",
        "leadIDMVA                :=leadingView.phoIdMvaWrtChosenVtx",
        "subleadIDMVA             :=subLeadingView.phoIdMvaWrtChosenVtx",
        "DiphotonMVA              :=diPhotonMVA.mvaValue()",
        "decorrSigmaM             :=diPhotonMVA.decorrSigmarv"
        ]


# Set category
cats = [
    ("All","1",0),
    ("UntaggedTag","1",4)
]

import flashgg.Taggers.dumperConfigTools as cfgTools

cfgTools.addCategory(process.diphotonDumper,
        "Reject",
        #                     "!leadingPhoton.hasMatchedGenPhoton() || !subLeadingPhoton.hasMatchedGenPhoton() ||"
        "abs(leadingPhoton.superCluster.eta)>=1.4442&&abs(leadingPhoton.superCluster.eta)<=1.566||abs(leadingPhoton.superCluster.eta)>=2.5"
        "||abs(subLeadingPhoton.superCluster.eta)>=1.4442 && abs(subLeadingPhoton.superCluster.eta)<=1.566||abs(subLeadingPhoton.superCluster.eta)>=2.5",
        -1 ## if nSubcat is -1 do not store anythings
        )

cfgTools.addCategories(process.diphotonDumper,
        ## categories definition
        ## cuts are applied in cascade. Events getting to these categories have already failed the "Reject" selection
        cats,
        ## variables to be dumped in trees/datasets. Same variables for all categories
        ## if different variables wanted for different categories, can add categorie one by one with cfgTools.addCategory
        variables=untagged_variables,
        ## histograms to be plotted. 
        ## the variables need to be defined first
        histograms=["CMS_hgg_mass>>mass(320,100,180)",
            "subleadPt:leadPt>>ptSubVsLead(180,20,200:180,20,200)",
            "minR9>>minR9(110,0,1.1)",
            "maxEta>>maxEta[0.,0.1,0.2,0.3,0.4,0.6,0.8,1.0,1.2,1.4442,1.566,1.7,1.8,2.,2.2,2.3,2.5]"
            ]
        )

# Met Filters
process.load('flashgg/Systematics/flashggMetFilters_cfi')

if customize.processId == "Data":
    metFilterSelector = "data"
    filtersInputTag = cms.InputTag("TriggerResults", "", "RECO")
else:
    metFilterSelector = "mc"
    filtersInputTag = cms.InputTag("TriggerResults", "", "PAT")

process.flashggMetFilters.requiredFilterNames = cms.untracked.vstring([filter.encode("ascii") for filter in customize.metaConditions["flashggMetFilters"][metFilterSelector]])
process.flashggMetFilters.filtersInputTag = filtersInputTag

### Final path
process.p = cms.Path(  
        process.flashggMetFilters
      * process.flashggDifferentialPhoIdInputsCorrection
      * process.flashggDiPhotonSystematics
      * process.flashggUnpackedJets
      * process.flashggTagSequence
      * process.diphotonDumper
                     )


# call the customization
customize(process)
