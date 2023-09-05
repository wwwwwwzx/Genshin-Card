# %% request data
from functools import partial
from PIL import Image, ImageFont, ImageDraw
import os, asyncio, requests
import genshin

UID = 900003924
Chinese = False  # 国服选True? 未测试
brower = "edge"  # chrome, edge, choromium, firefox, opera，有登录mys/hoyolab账号的浏览器
out_image_path = "box_v3.png"  # 输出文件名
myfont = "zh-cn.ttf"  # 字体文件
new = False  # 是否重新请求数据


# %% =====================================
async def main():
    cache = []
    client = genshin.Client(region=genshin.Region.CHINESE) if Chinese else genshin.Client(lang="zh-cn")

    try:
        client.set_browser_cookies(brower)
    except PermissionError:
        print("请关闭浏览器后重试")
        exit(1)
    data = await client.get_genshin_user(UID)

    def is_cons_talent(character, talent):  # if talent +3
        if character.constellation < 3:
            return False
        if talent.name in character.constellations[2].effect:
            return True
        if character.constellation < 5:
            return False
        return talent.name in character.constellations[4].effect

    for character in data.characters:
        found = False
        while not found:
            try:
                details = await client.get_character_details(character.id)
                item = details.__dict__ | character.__dict__
                t = 0
                talents = []
                for talent in item["talents"]:
                    if talent.upgradeable:
                        if is_cons_talent(character, talent):
                            talents.append((talent.level, 3))
                        else:
                            talents.append((talent.level, 0))
                        t += 1
                item["weapon"] = item["weapon"].__dict__
                item["talents"] = talents
                id = character.id % 1000
                if id in [5, 7]:  # traveler
                    item["name"] = "荧" if id == 7 else "空"
                    item["friendship"] = 10
                found = True
            except Exception as e:
                print(e)
                print(character.name)
                await asyncio.sleep(3)
        cache.append(item)
    return cache


# colors
conscolor = {
    0: (96, 94, 105, 255),
    1: (94, 188, 198, 255),
    2: (51, 162, 96, 255),
    3: (61, 149, 185, 255),
    4: (60, 86, 181, 255),
    5: (110, 73, 168, 255),
    6: (254, 83, 27, 255),
}


def talentcolor(x):
    if x == 10:
        return (255, 135, 132, 255)
    elif x == 9:
        return (192, 166, 255, 255)
    elif x >= 6:
        return (137, 181, 226, 255)
    else:
        return (96, 94, 105, 255)


black = (0, 0, 0, 255)
raritycolor = {
    5: (255, 240, 211, 255),
    4: (225, 204, 245, 255),
    3: (206, 215, 246, 255),
}


# Cache folder
icon_folder = os.path.dirname(__file__) + r"\icons"
if not os.path.exists(icon_folder):
    os.makedirs(icon_folder)

# font
try:
    font = partial(ImageFont.truetype, font=myfont)
    font(size=1)  # 字体文件测试
except OSError:
    print("未找到字体文件，使用默认字体")
    font = partial(ImageFont.truetype, font="msyhbd.ttc")
    font(size=1)


def sort_cache(cache):
    cache.sort(key=lambda x: x["id"], reverse=True)
    cache.sort(key=lambda x: x["weapon"]["rarity"], reverse=True)
    cache.sort(key=lambda x: x["constellation"], reverse=True)
    cache.sort(key=lambda x: x["talents"], reverse=True)
    cache.sort(key=lambda x: x["friendship"], reverse=True)
    cache.sort(key=lambda x: x["level"], reverse=True)
    cache.sort(key=lambda x: x["rarity"], reverse=True)


if new:
    cache = asyncio.run(main())
    sort_cache(cache)

    try:
        import yaml

        def clean_dict(obj):
            if isinstance(obj, dict):
                return {k: clean_dict(v) for k, v in obj.items() if v is not None}
            elif isinstance(obj, list):
                return [clean_dict(v) for v in obj if v is not None]
            elif hasattr(obj, "__dict__"):
                return clean_dict(obj.__dict__)
            else:
                return obj

        yaml.safe_dump(dict(cache=clean_dict(cache)), open("cache.yml", "w", encoding="utf-8"), sort_keys=False, allow_unicode=True)
    except Exception as e:
        import pickle

        with open("cache.bin", "wb") as outfile:
            pickle.dump(cache, outfile)
else:
    import yaml

    cache = yaml.safe_load(open("cache.yml", encoding="utf-8"))["cache"]


sort_cache(cache)


def getimage(obj):
    imagefile = icon_folder + "//" + obj["name"] + ".png"
    if os.path.exists(imagefile):
        return Image.open(imagefile)
    else:
        print("下载图片资源: " + obj["name"] + ".png")
        try:
            im = Image.open(requests.get(obj["icon"], stream=True).raw)
            im.save(imagefile, "PNG")
        except Exception as e:
            print(e)
            print("下载失败: " + obj["name"] + ".png")
            return Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        return im


def resizeimage(img, w, h):
    if w < h:
        return img.convert("RGBA").resize((h, h), Image.Resampling.LANCZOS).crop(((h - w) / 2, 0, (w + h) / 2, h))
    else:
        return img.convert("RGBA").resize((w, w), Image.Resampling.LANCZOS).crop((0, (w - h) / 2, w, (w + h) / 2))


N = len(cache)
N5 = len([c for c in cache if c["rarity"] == 5])
N4 = N - N5
unit = lambda x: int(x * 50)
col_width = unit(20)
Unit = unit(1)
Space = unit(1.2)
card = Image.new("RGBA", (col_width * 2, Space * max(N5, N4) + unit(4.8)), (255, 255, 255, 255))
draw = ImageDraw.Draw(card)

cnt_10 = 0
cnt_9 = 0
cnt_6 = 0
for ii, c in enumerate(cache):
    y = Space * ii + unit(4)
    imy = y - unit(0.6)
    x_ofs, y_ofs = (col_width, -unit(N5 * 1.2)) if ii >= N5 else (0, 0)
    if ii == 0:
        for x0 in (0, col_width):
            y0 = y - Space
            title_color = (205, 182, 140, 255)
            titlebg = Image.new("RGBA", (col_width - unit(0.5), unit(1.2)), (59, 58, 64, 255))
            card.paste(titlebg, (unit(0.2) + x0, y0 - unit(0.6)))
            locs = (0.5, 2.5, 5, 6, 7, 8, 9, 10, 13.5)
            titles = ["#", "角色", "Lv", "命座", "好感", "A", "E", "Q", "武器"]
            fontsize = [0.4, 0.6, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.6]
            for loc, t, s in zip(locs, titles, fontsize):
                draw.text((loc * Space + x0, y0), t, font=font(size=unit(s)), fill=title_color, anchor="mm")
    chbg = Image.new("RGBA", (unit(5), unit(1.2)), raritycolor[c["rarity"]])
    card.paste(chbg, (unit(0.2) + x_ofs, imy + y_ofs))
    icon = resizeimage(getimage(c), Unit, Unit)
    draw.text((unit(0.6) + x_ofs, y + y_ofs), str(ii + 1), font=font(size=unit(0.4)), fill=black, anchor="mm")
    card.paste(icon, (Unit + x_ofs, imy + y_ofs), icon)
    draw.text((3 * Space + x_ofs, y + y_ofs), c["name"], font=font(size=unit(0.55)), fill=black, anchor="mm")
    draw.text((5 * Space + x_ofs, y + y_ofs), str(c["level"]), font=font(size=unit(0.6)), fill=black, anchor="mm")
    conbg = Image.new("RGBA", (unit(0.6), unit(0.9)), conscolor[c["constellation"]])
    card.paste(conbg, (unit(6.9) + x_ofs, imy + unit(0.1) + y_ofs))
    draw.text((6 * Space + x_ofs, y + y_ofs), str(c["constellation"]), font=font(size=unit(0.6)), fill=(255, 255, 255, 255), anchor="mm")
    draw.text((7 * Space + x_ofs, y + y_ofs), str(c["friendship"]), font=font(size=unit(0.6)), fill=(235, 107, 132, 255), anchor="mm")
    for ii, (t1, t2) in enumerate(c["talents"]):
        tbg = Image.new("RGBA", (unit(1.2), unit(1.2)), talentcolor(t1))
        card.paste(tbg, (unit(9.1 + ii * 1.2) + x_ofs, imy + y_ofs))
        if c["id"] % 1000 == 33 and ii == 0:  # "达达利亚"
            t2 = 1
        if t1 == 10:
            cnt_10 += 1
        elif t1 >= 9:
            cnt_9 += 1
        elif t1 >= 6:
            cnt_6 += 1
        draw.text(
            (8.1 * Space + ii * Space + x_ofs, y + y_ofs),
            str(t1 + t2),
            font=font(size=unit(0.6)),
            fill=((161, 8, 10, 255) if t1 == 10 else (125, 42, 94, 255)) if t2 > 0 else black,
            anchor="mm",
        )
    draw.text(
        (7 * Space + x_ofs, y + y_ofs),
        str(c["friendship"]),
        font=font(size=unit(0.6)),
        fill=(235, 107, 132, 255) if c["friendship"] == 10 else black,
        anchor="mm",
    )

    w = c["weapon"]
    chbg = Image.new("RGBA", (unit(7), unit(1.2)), raritycolor[w["rarity"]])
    card.paste(chbg, (unit(12.7) + x_ofs, imy + y_ofs))
    draw.text((unit(13.1) + x_ofs, y + unit(0.05) + y_ofs), "Lv", font=font(size=unit(0.3)), fill=black, anchor="mm")
    draw.text((unit(13.7) + x_ofs, y + y_ofs), str(w["level"]), font=font(size=unit(0.5)), fill=black, anchor="mm")
    refbg = Image.new("RGBA", (unit(0.5), unit(0.7)), conscolor[w["refinement"] + 1])
    card.paste(refbg, (unit(15.2) + x_ofs, imy + unit(0.2) + y_ofs))
    draw.text((unit(15.45) + x_ofs, y + y_ofs), str(w["refinement"]), font=font(size=unit(0.4)), fill=(255, 255, 255, 255), anchor="mm")
    draw.text((unit(17.5) + x_ofs, y + y_ofs), w["name"], font=font(size=unit(0.5)), fill=black, anchor="mm")
    wicon = resizeimage(getimage(w), Unit, Unit)
    card.paste(wicon, (unit(14.1) + x_ofs, imy + y_ofs), wicon)

draw.text((unit(0.6), unit(0.2)), f"UID: {UID}", font=font(size=unit(0.6)), fill=black)
draw.text((col_width * 2 - unit(0.4), unit(0.2)), f"共{N}名角色", font=font(size=unit(0.6)), fill=black, anchor="rt")
cnt_0 = N * 3 - cnt_10 - cnt_9 - cnt_6
l0 = unit(0.2)
total = 39.5
draw.text((l0 + unit(total / 2), unit(1)), "天赋进度条", font=font(size=unit(0.6)), fill=black, anchor="mm")
for cnt, clr in zip([cnt_0, cnt_6, cnt_9, cnt_10], [0, 6, 9, 10]):
    l = total * cnt / (N * 3)
    card.paste(Image.new("RGBA", (unit(l), unit(0.9)), talentcolor(clr)), (l0, unit(1.4)))
    if cnt:
        draw.text((l0, unit(1.3)), f"{clr}", font=font(size=unit(0.4)), fill=talentcolor(clr), anchor="mm")
        draw.text((l0 + unit(l / 2), unit(2)), f"{cnt}", font=font(size=unit(0.4)), fill=black, anchor="mm")
    l0 += unit(l)
from datetime import datetime

draw.text((col_width * 2 - unit(0.4), Space * max(N5, N4) + unit(3.8)), datetime.now().strftime("%Y/%m/%d"), font=font(size=unit(0.7)), fill=black, anchor="rt")
card.save(out_image_path, "PNG")
os.startfile(out_image_path)
