from discord import Embed
import brawlstats

def badEmbed(text):
    bembed = Embed(color=0xff0000)
    bembed.set_author(name=text, icon_url="https://i.imgur.com/dgE1VCm.png")
    return bembed
    
def goodEmbed(text):
    gembed = Embed(color=0x45cafc)
    gembed.set_author(name=text, icon_url="https://i.imgur.com/fSAGoHh.png")
    return gembed

club_status = {
    "inviteonly" : {"name": "Invite Only", "emoji": "<:invite_only:729734736490266625>"},
    "closed" : {"name": "Closed", "emoji": "<:locked:729734736573890570>"},
    "open" : {"name": "Open", "emoji": "<:open:729734736695787564> "}
}

ids = {
    'supercityrampage': 16, 
    'hotzone': 15, 
    'presentplunder': 14, 
    'gemgrab': 2, 
    'showdown': 3, 
    'duoshowdown': 4, 
    'heist': 5, 
    'bounty': 1, 
    'brawlball': 7, 
    'siege': 10, 
    'takedown': 12, 
    'lonestar': 13, 
    'roborumble': 8, 
    'biggame': 6, 
    'bossfight': 9, 
    'training': 11
}

def get_gamemode_id(name):
    try:
        return ids[name.lower().replace("-", "").replace(" ", "")]
    except KeyError:
        return None

gamemodes = {
    "1": "<:Bounty:729650154638016532>",
    "2": "<:GemGrab:729650153388114002>",
    "3": "<:Showdown:729650153669132359>",
    "4": "<:DuoShowdown:729650154092625970>",
    "5": "<:Heist:729650154139025449>",
    "6": "<:BigGame:729650157787807756>",
    "7": "<:BrawlBall:729650154919034882>",
    "8": "<:RoboRumble:729650158106574898>",
    "9": "<:BossFight:729650158098448464>",
    "10": "<:Siege:729650155673878558>",
    "11": "", #training cave
    "12": "<:Takedown:729650156382978088>",
    "13": "<:LoneStar:729650156491767849>",
    "14": "<:PresentPlunder:729650153203433554>",
    "15": "<:HotZone:729650153723789413>",
    "16": "<:SuperCityRampage:729650153203433582>"
}

def get_gamemode_emoji(id):
    try:
        return gamemodes[str(id)]
    except KeyError:
        return ""

def get_league_emoji(trophies : int):
    if trophies < 500:
        return "<:league_icon_00:553294108802678787>"
    elif trophies < 1000:
        return "<:league_icon_01:553294108735569921>"
    elif trophies < 2000:
        return "<:league_icon_02:553294109167583296>"
    elif trophies < 3000:
        return "<:league_icon_03:553294109264052226>"
    elif trophies < 4000:
        return "<:league_icon_04:553294344413511682>"
    elif trophies < 6000:
        return "<:league_icon_05:553294344912764959>"
    elif trophies < 8000:
        return "<:league_icon_06:553294344841461775>"
    elif trophies < 10000:
        return "<:league_icon_07:553294109515972640>"
    elif trophies < 16000:
        return "<:league_icon_08:553294109217914910>"
    elif trophies < 30000:
        return "<:league_icon_09:729644184616828928>"
    elif trophies < 50000:
        return "<:league_icon_10:729644185199575140>"
    else:
        return "<:league_icon_11:729644185778520115>"

def get_rank_emoji(rank : int):
    if 1 <= rank < 5:
        return "<:rank1:664262410265165824>"
    elif 5 <= rank < 10:
        return "<:rank5:664262466812772377>"
    elif 10 <= rank < 15:
        return "<:rank10:664262501344608257>"
    elif 15 <= rank < 20:
        return "<:rank15:664262551139254312>"
    elif 20 <= rank < 25:
        return "<:rank20:664262586266681371>"
    elif 25 <= rank < 30:
        return "<:rank25:664262630223118357> "
    elif 30 <= rank < 35:
        return "<:rank30:664262657557397536>"
    elif 35 <= rank:
        return "<:rank35:664262686028333056>"

def get_brawler_emoji(name : str):
    if name == "SHELLY":
        return "<:shelly:664235199076237323>"
    elif name == "TICK":
        return "<:tick:664235450889928744>"
    elif name == "TARA":
        return "<:tara:664236127015796764>"
    elif name == "SPIKE":
        return "<:spike:664235867748958249>"
    elif name == "SANDY":
        return "<:sandy:664235310573420544>"
    elif name == "ROSA":
        return "<:rosa:664235409722834954>"
    elif name == "RICO":
        return "<:rico:664235890171707393>"
    elif name == "EL PRIMO":
        return "<:primo:664235742758830135>"
    elif name == "POCO":
        return "<:poco:769133920784482324>"
    elif name == "PIPER":
        return "<:piper:664235622998867971>"
    elif name == "PENNY":
        return "<:penny:664235535094644737>"
    elif name == "PAM":
        return "<:pam:769132131552854018>"
    elif name == "NITA":
        return "<:nita:664235795959513088>"
    elif name == "MORTIS":
        return "<:mortis:664235717693800468>"
    elif name == "MAX":
        return "<:max:769131218125586442>"
    elif name == "LEON":
        return "<:leon:664235430530514964>"
    elif name == "JESSIE":
        return "<:jessie:664235816339636244>"
    elif name == "GENE":
        return "<:gene:664235476084981795>"
    elif name == "FRANK":
        return "<:frank:664235513242320922>"
    elif name == "EMZ":
        return "<:emz:664235245956235287>"
    elif name == "DYNAMIKE":
        return "<:dynamike:664235766620094464>"
    elif name == "DARRYL":
        return "<:darryl:769133920783826944>"
    elif name == "CROW":
        return "<:crow:769133920759316530>"
    elif name == "COLT":
        return "<:colt:664235956202766346>"
    elif name == "CARL":
        return "<:carl:664235388537274369>"
    elif name == "BULL":
        return "<:bull:664235934006378509>"
    elif name == "BROCK":
        return "<:brock:664235912150122499>"
    elif name == "BO":
        return "<:bo:664235645287530528>"
    elif name == "BIBI":
        return "<:bibi:664235367615954964>"
    elif name == "BEA":
        return "<:bea:664235276758941701>"
    elif name == "BARLEY":
        return "<:barley:664235839316033536>"
    elif name == "8-BIT":
        return "<:8bit:664235332522213418>"
    elif name == "MR. P":
        return "<:mrp:671379771585855508>"
    elif name == "JACKY":
        return "<:jackie:697096353494597642>"
    elif name == "SPROUT":
        return "<:sprout:705235612890038282>"
    elif name == "GALE":
        return "<:gale:710492017905500191>"
    elif name == "NANI":
        return "<:nani:718555376340959242>"
    elif name == "SURGE":
        return "<:surge:729632664218238986>"
    elif name == "COLETTE":
        return "<:colette:753659575424516287>"
    elif name == "AMBER":
        return "<:amber:769131126773907498>"
    elif name == "LOU":
        return "<:lou:777831488930054169>"
    elif name == "BYRON":
        return "<:byron:788738414442053662>"
    elif name == "EDGAR":
        return "<:edgar:788751655436943361>"
    elif name == "COLONEL RUFFS":
        return "<:ruffs:803995640543313972>"
    elif name == "STU":
        return "<:stu:820963374706982923>"
    else:
        return "<:__:452891824168894494>"
    
def remove_codes(text : str):
    toremove = ["</c>", "<c1>", "<c2>", "<c3>", "<c4>", "<c5>", "<c6>", "<c7>", "<c8>", "<c9>", "<c0>"]
    for code in toremove:
        text = text.replace(code, "")
    return text

def calculate_starpoints(player : brawlstats.models.Player):
    total = 0
    for b in player.raw_data['brawlers']:
        trophies = b['trophies']
        if trophies <= 500:
            total += 0
        elif trophies < 525:
            total += 20
        elif trophies < 550:
            total += 50
        elif trophies < 575:
            total += 70
        elif trophies < 600:
            total += 80        
        elif trophies < 625:
            total += 90        
        elif trophies < 650:
            total += 100  
        elif trophies < 675:
            total += 110        
        elif trophies < 700:
            total += 120       
        elif trophies < 725:
            total += 130        
        elif trophies < 750:
            total += 140        
        elif trophies < 775:
            total += 150       
        elif trophies < 800:
            total += 160
        elif trophies < 825:
            total += 170
        elif trophies < 850:
            total += 180
        elif trophies < 875:
            total += 190
        elif trophies < 900:
            total += 200
        elif trophies < 925:
            total += 210
        elif trophies < 950:
            total += 220
        elif trophies < 975:
            total += 230
        elif trophies < 1000:
            total += 240
        elif trophies < 1050:
            total += 250
        elif trophies < 1100:
            total += 260
        elif trophies < 1150:
            total += 270
        elif trophies < 1200:
            total += 280
        elif trophies < 1250:
            total += 290
        elif trophies < 1300:
            total += 300
        elif trophies < 1350:
            total += 310
        elif trophies < 1400:
            total += 320
        elif trophies < 1450:
            total += 330
        elif trophies < 1500:
            total += 340
        else:
            total += 350
    return total


def reset_trophies(player : brawlstats.models.Player):
    total = 0
    for b in player.raw_data['brawlers']:
        trophies = b['trophies']
        if trophies <= 500:
            total += trophies
        elif trophies < 525:
            total += 500
        elif trophies < 550:
            total += 524
        elif trophies < 575:
            total += 549
        elif trophies < 600:
            total += 574       
        elif trophies < 625:
            total += 599        
        elif trophies < 650:
            total += 624  
        elif trophies < 675:
            total += 649        
        elif trophies < 700:
            total += 674       
        elif trophies < 725:
            total += 699        
        elif trophies < 750:
            total += 724        
        elif trophies < 775:
            total += 749       
        elif trophies < 800:
            total += 774
        elif trophies < 825:
            total += 799
        elif trophies < 850:
            total += 824
        elif trophies < 875:
            total += 849
        elif trophies < 900:
            total += 874
        elif trophies < 925:
            total += 885
        elif trophies < 950:
            total += 900
        elif trophies < 975:
            total += 920
        elif trophies < 1000:
            total += 940
        elif trophies < 1050:
            total += 960
        elif trophies < 1100:
            total += 980
        elif trophies < 1150:
            total += 1000
        elif trophies < 1200:
            total += 1020
        elif trophies < 1250:
            total += 1040
        elif trophies < 1300:
            total += 1060
        elif trophies < 1350:
            total += 1080
        elif trophies < 1400:
            total += 1100
        elif trophies < 1450:
            total += 1120
        elif trophies < 1500:
            total += 1140
        else:
            total += 1150
    return total

def get_power_league(league):
    number = str(3 if league % 3 == 0 else league % 3)
    if league <= 3:
        return "<:bronze:822502621138911312> Bronze " + number
    elif league <= 6:
        return "<:silver:822502621092511854> Silver " + number
    elif league <= 9:
        return "<:gold:822502621310484490> Gold " + number
    elif league <= 12:
        return "<:diamond:822502621364748288> Diamond " + number
    elif league <= 15:
        return "<:mythic:822502621108502599> Mythic " + number
    elif league <= 18:
        return "<:legendary:822502621351903252> Legendary " + number
    else:
        return "<:masters:822502621663199252> Masters "
