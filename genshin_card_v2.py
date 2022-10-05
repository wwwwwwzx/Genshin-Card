import os, asyncio, requests, subprocess, platform, datetime
from PIL import Image, ImageFont, ImageDraw
import genshin

# version 2.0

mysid = 12769246  # Hoyolab or 米游社ID
Chinese = False  # 国服选True
BgImage = "bg2.png"  # 背景图片文件名
colmax = 8  # 每行角色数


async def main():
    if Chinese:
        client = genshin.Client(region=genshin.Region.CHINESE)
    else:
        client = genshin.Client(lang='zh-cn')

    client.set_cache(maxsize=256, ttl=3600)
    client.cache = genshin.StaticCache()

    client.set_browser_cookies('chrome')
    user = (await client.get_record_cards(mysid))[0]
    data = await client.get_genshin_user(user.uid)
    abyss = await client.get_spiral_abyss(user.uid)

    rowmax = len(data.characters) // colmax + 1
    startx = 12
    spacex1 = 2
    spacex2 = 12
    starty = 10
    spacey = 12
    # character card size
    sizex, sizey = 100, 100
    # weapon card size
    wpx, wpy = 36, 36
    # info card width
    infox = 75

    def getimage(url):
        imagefile = 'icons/' + os.path.basename(url)
        if os.path.exists(imagefile):
            return Image.open(imagefile)
        else:
            print("Downloading " + os.path.basename(url))
            im = Image.open(requests.get(url, stream=True).raw)
            im.save(imagefile, "PNG")
            return im

    def resizeimage(img, w, h):
        if w < h:
            return img.convert("RGBA").resize((h, h), Image.Resampling.LANCZOS).crop(((h - w) / 2, 0, (w + h) / 2, h))
        else:
            return img.convert("RGBA").resize((w, w), Image.Resampling.LANCZOS).crop((0, (w - h) / 2, w, (w + h) / 2))

    elementlist = ['Geo', 'Anemo', 'Cryo', 'Electro', 'Dendro', 'Hydro', 'Pyro']
    eleicons = []
    for ele in elementlist:
        eleicons.append(resizeimage(Image.open('icons/' + ele + '.png'), 25, 25))

    def elementorder(ele):
        return elementlist.index(ele)

    def checkcons(character, talent):
        if character.constellation < 3:
            return False
        elif character.constellation > 4:
            return True
        else:
            return talent.name in character.constellations[2].effect

    cardx = startx * 2 + (sizex + spacex1 + infox + spacex2) * colmax - spacex2
    cardy = starty * 2 + (sizey + spacey) * rowmax - 10
    confont = ImageFont.truetype("zh-cn.ttf", 20)
    notefont = ImageFont.truetype("zh-cn.ttf", 12)
    lvlfont = ImageFont.truetype("zh-cn.ttf", 13)
    talentfont = ImageFont.truetype("zh-cn.ttf", 14)
    weaponfont = ImageFont.truetype("zh-cn.ttf", 11)
    flfont = ImageFont.truetype("zh-cn.ttf", 10)
    conbg = Image.new("RGBA", (20, 27), (70, 70, 70, 200))
    l4bg = resizeimage(Image.open('icons/level_4.png'), sizex, sizey)
    l5bg = resizeimage(Image.open('icons/level_5.png'), sizex, sizey)
    wbgs = [resizeimage(Image.open(f'icons/level_{ii}.png'), wpx, wpy) for ii in range(1, 6)]
    spbg = resizeimage(Image.open('icons/sp.png'), sizex, sizey)
    flicon = resizeimage(Image.open('icons/FL.png'), 18, 18)
    talentcolor = (33, 157, 235)
    # defaultcolor = [(180,166,120),(77,160,50),(30,143,245),(221,57,48)]
    defaultcolor = [(134, 134, 134), (58, 133, 185), (127, 93, 177), (202, 71, 77)]

    def getalpha(img, rad, corner=[1, 1, 1, 1]):
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        ImageDraw.Draw(circle).ellipse((0, 0, rad * 2, rad * 2), fill=255)
        w, h = img.size
        mask = Image.new("L", img.size, 255)

        if corner[0]:
            mask.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        if corner[1]:
            mask.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        if corner[2]:
            mask.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        if corner[3]:
            mask.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        return mask

    def colorlevel(lvl, std, colortable=defaultcolor):
        if lvl >= std[2]:
            return colortable[3]
        elif lvl >= std[1]:
            return colortable[2]
        elif lvl >= std[0]:
            return colortable[1]
        else:
            return colortable[0]

    sign = Image.open(BgImage).resize((cardx, cardy), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(sign)
    for idx, character in enumerate(data.characters):
        row = idx // colmax
        col = idx % colmax
        x = startx + col * (sizex + spacex1 + infox + spacex2)
        y = starty + row * (sizey + spacey)
        if idx < 4:
            holo = Image.new("RGB", (sizex + spacex1 + infox, sizey + 6), (0, 255, 0))
            sign.paste(holo, (x, y - 2), getalpha(holo, 12, [1, 1, 1, 1]))
        card = Image.new("RGBA", (sizex, sizey), (0, 0, 0, 0))
        carddraw = ImageDraw.Draw(card)
        if character.collab:
            card.paste(spbg, (0, 0))
        elif character.rarity == 4:
            card.paste(l4bg, (0, 0))
        else:
            card.paste(l5bg, (0, 0))
        im = resizeimage(getimage(character.icon), sizex, sizey)
        card.paste(im, (0, 0), im)
        if character.element != '':
            eleim = eleicons[elementorder(character.element)]
            card.paste(eleim, (2, 2), eleim)
        if character.constellation > 0:
            card.paste(conbg, (sizex - 19, 0), conbg)
            carddraw.text((sizex - 9, 15),
                          str(character.constellation),
                          colorlevel(character.constellation, [1, 3, 6], colortable=[(204, 180, 132), (240, 235, 227), (255, 215, 0), (252, 156, 45)]),
                          font=confont,
                          anchor='mm')
        sign.paste(card, (x, y), getalpha(card, 16, [1, 1, 0, 0]))
        # %% friendship and level
        infocard = Image.new("RGBA", (infox, sizey), (240, 235, 227, 200))
        infodraw = ImageDraw.Draw(infocard)
        if character.friendship == 0:
            infodraw.text((infox / 2, sizey / 7), 'Lv.' + str(character.level), colorlevel(character.level, [80, 89, 90]), font=lvlfont, anchor='mm')
        else:
            infodraw.text((infox / 3 - 1, sizey / 7), 'Lv.' + str(character.level), colorlevel(character.level, [70, 80, 90]), font=lvlfont, anchor='mm')
            infocard.paste(flicon, (sizex - 56, 5), flicon)
            infodraw.text((infox - 8, sizey / 7),
                          str(character.friendship),
                          colorlevel(character.friendship, [6, 8, 10]),
                          font=flfont if character.friendship == 10 else lvlfont,
                          anchor='mm')
        # %% talent
        try:
            details = await client.get_character_details(character.id)
            t = 0
            for talent in details.talents:
                if talent.upgradeable:
                    if t > 0 and checkcons(character, talent):
                        # infocard.paste(Image.new("RGB", (18,18), talentcolor),(3 + int(infox/3 * t), int(sizey*3/8) - 10))
                        infodraw.text((infox / 6 + infox / 3 * t + 5, sizey * 3 / 8 - 9), "+3", talentcolor, font=flfont, anchor='mm')
                    infodraw.text((infox / 6 + infox / 3 * t, sizey * 3 / 8 + 2),
                                  str(talent.level),
                                  colorlevel(talent.level, [6, 8, 10]),
                                  font=talentfont,
                                  anchor='mm')
                    t += 1
        except:
            pass
        # %% weapon
        infocard.paste(wbgs[character.weapon.rarity - 1], (4, int(infox / 2) + 15))
        im = resizeimage(getimage(character.weapon.icon), wpx, wpy)
        infocard.paste(im, (4, int(infox / 2) + 15), im)
        infodraw.text((infox * 3 / 4, sizey * 5 / 8),
                      'Lv' + str(character.weapon.level),
                      colorlevel(character.weapon.level, [70, 80, 90]),
                      font=weaponfont,
                      anchor='mm')
        infodraw.text((infox * 3 / 4, sizey * 0.8),
                      str(character.weapon.refinement) + ' 阶',
                      colorlevel(character.weapon.refinement + character.weapon.rarity - 4, [1, 3, 5]),
                      font=weaponfont,
                      anchor='mm')

        sign.paste(infocard, (x + spacex1 + sizex, y), getalpha(infocard, 16, corner=[0, 0, 1, 1]))


# %% Player
    draw.text((cardx - infox - sizex - spacex2, cardy - 115),
              f"{user.nickname}  AR {user.level}    活跃天数: {data.stats.days_active}", (255, 255, 255),
              font=notefont)
    draw.text((cardx - infox - sizex - spacex2, cardy - 96),
              f"满好感: {sum(c.friendship == 10 for c in data.characters)}/{data.stats.characters - 1}   成就数: {data.stats.achievements}", (255, 255, 255),
              font=notefont)
    draw.text((cardx - infox - sizex - spacex2, cardy - 77),
              f"深境螺旋: {abyss.max_floor} {abyss.total_battles}次 {abyss.total_stars}星", (255, 255, 255),
              font=notefont)
    draw.text((cardx - infox - sizex - spacex2, cardy - 58),
              f"宝箱数:{data.stats.luxurious_chests} | {data.stats.precious_chests} | {data.stats.exquisite_chests} | {data.stats.common_chests}", (255, 255, 255),
              font=notefont)
    draw.text((cardx - 123, cardy - 20), f"UID: {user.uid}", (255, 255, 255), font=notefont)
    draw.text((cardx - 90, cardy - 39), datetime.datetime.now().strftime("%Y/%m/%d"), font=notefont)

    sign.save("box.png", "PNG")
    if platform.system() == 'Darwin':  # macOS
        subprocess.call(('open', "box.png"))
    elif platform.system() == 'Windows':  # Windows
        os.startfile("box.png")
    else:  # linux variants
        subprocess.call(('xdg-open', "box.png"))

asyncio.run(main())
