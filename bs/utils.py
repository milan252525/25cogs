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
    else:
        return "<:league_icon_08:553294109217914910>"

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
        return "<:poco:664235668393689099>"
    elif name == "PIPER":
        return "<:piper:664235622998867971>"
    elif name == "PENNY":
        return "<:penny:664235535094644737>"
    elif name == "PAM":
        return "<:pam:664235599804235786>"
    elif name == "NITA":
        return "<:nita:664235795959513088>"
    elif name == "MORTIS":
        return "<:mortis:664235717693800468>"
    elif name == "MAX":
        return "<:max:664235224762155073>"
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
        return "<:darryl:664235555877290008>"
    elif name == "CROW":
        return "<:crow:664235693064716291>"
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
    
def remove_codes(text : str):
    toremove = ["</c>", "<c1>", "<c2>", "<c3>", "<c4>", "<c5>", "<c6>", "<c7>", "<c8>", "<c9>", "<c0>"]
    for code in toremove:
        text = text.replace(code, "")
    return text

def calculate_starpoints(player : brawlstats.models.Player):
    total = 0
    for b in player.raw_data['brawlers']:
        if 550 <= b.get('trophies') <= 599:
            total = total + 70
        elif 600 <= b.get('trophies') <= 649:
            total = total + 120
        elif 650 <= b.get('trophies') <= 699:
            total = total + 160
        elif 700 <= b.get('trophies') <= 749:
            total = total + 200
        elif 750 <= b.get('trophies') <= 799:
            total = total + 220
        elif 800 <= b.get('trophies') <= 849:
            total = total + 240
        elif 850 <= b.get('trophies') <= 899:
            total = total + 260
        elif 900 <= b.get('trophies') <= 949:
            total = total + 280
        elif 950 <= b.get('trophies') <= 999:
            total = total + 300
        elif 1000 <= b.get('trophies') <= 1049:
            total = total + 320
        elif 1050 <= b.get('trophies') <= 1099:
            total = total + 340
        elif 1100 <= b.get('trophies') <= 1149:
            total = total + 360
        elif 1150 <= b.get('trophies') <= 1199:
            total = total + 380
        elif 1200 <= b.get('trophies') <= 1249:
            total = total + 400
        elif 1250 <= b.get('trophies') <= 1299:
            total = total + 420
        elif 1300 <= b.get('trophies') <= 1349:
            total = total + 440
        elif 1350 <= b.get('trophies') <= 1399:
            total = total + 460
        elif 1400 <= b.get('trophies'):
            total = total + 480
    return total
