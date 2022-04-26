import genshin, os, asyncio

# version 1.00

mysid = 12769246 # Hoyolab or 米游社ID
Chinese = False # 国服选True
BgImage = "bg2.png" # 背景图片文件名
colmax = 10 # 每行角色数

async def main():
	if Chinese:
		client = genshin.Client(region=genshin.Region.CHINESE)
	else:
		client = genshin.Client(lang = 'zh-cn')

	client.set_browser_cookies()
	user = (await client.get_record_cards(mysid))[0]
	data = await client.get_genshin_user(user.uid)
	abyss = await client.get_spiral_abyss(user.uid)
	# explorations = data.explorations
	# print(explorations)
	
	rowmax = len(data.characters)// colmax + 1
	startx = 12
	spacex = 12
	starty = 10
	spacey = 33
	sizex = 112
	sizey = 112

	from PIL import Image, ImageFont, ImageDraw

	def getimage(url):
		imagefile = 'icons/' + os.path.basename(url)
		if os.path.exists(imagefile):
			return Image.open(imagefile)
		else:
			import requests
			print("Downloading " + os.path.basename(url))
			im = Image.open(requests.get(url, stream=True).raw)
			im.save(imagefile, "PNG")
			return im
	elementlist = ['Geo','Anemo','Cryo','Electro','Hydro','Pyro']
	eleicons = []
	for ele in elementlist:
		eleicons.append(Image.open('icons/' + ele + '.png').convert("RGBA").resize((25,25),Image.ANTIALIAS))
	def elementorder(ele):
		return elementlist.index(ele)
	
	cardx = startx * 2 + (sizex + spacex) * colmax - spacex
	cardy = starty * 2 + (sizey + spacey) * rowmax - 10
	confont = ImageFont.truetype("zh-cn.ttf", 20)
	notefont = ImageFont.truetype("zh-cn.ttf", 12)
	lvlfont = ImageFont.truetype("zh-cn.ttf", 14)
	talentfont = ImageFont.truetype("zh-cn.ttf", 10)
	flfont = ImageFont.truetype("zh-cn.ttf", 11)
	conbg = Image.new("RGBA", (20,25), (70, 70, 70, 200))
	l4bg = Image.open('icons/level_4.png').resize((sizey,sizey),Image.ANTIALIAS).crop(((sizey - sizex) / 2, 0, (sizey + sizex) / 2, sizey))
	l5bg = Image.open('icons/level_5.png').resize((sizey,sizey),Image.ANTIALIAS).crop(((sizey - sizex) / 2, 0, (sizey + sizex) / 2, sizey))
	spbg = Image.open('icons/sp.png').resize((sizey,sizey),Image.ANTIALIAS).crop(((sizey - sizex) / 2, 0, (sizey + sizex) / 2, sizey))
	flicon = Image.open('icons/FL.png').resize((21,21),Image.ANTIALIAS)

	rad = 24
	lvlbg = Image.new("RGB", (sizex,23 + rad), (240, 240, 240))
	circle = Image.new('L', (rad * 2, rad * 2), 0) 
	ImageDraw.Draw(circle).ellipse((0, 0, rad * 2, rad * 2), fill = 255)
	rad2 = 8
	circle2 = Image.new('L', (rad2 * 2, rad2 * 2), 0) 
	ImageDraw.Draw(circle2).ellipse((0, 0, rad2 * 2, rad2 * 2), fill = 255)
	alpha = Image.new('L', (sizex,sizey), 255)
	alpha.paste(circle2.crop((0, 0, rad2, rad2)), (0, 0))
	# alpha.paste(circle2.crop((0, rad2, rad2, rad2 * 2)), (0, sizey-rad2))
	alpha.paste(circle2.crop((rad2, 0, rad2 * 2, rad2)), (sizex-rad2, 0))
	alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (sizex-rad, sizey-rad))

	sign = Image.open(BgImage).resize((cardx, cardy),Image.ANTIALIAS)
	draw = ImageDraw.Draw(sign)

	row = 0
	col = 0
	flcnt = 0
	for character in data.characters:
		# print(f"{character['id']} - {character['name']}")
		if col == colmax:
			row = row + 1
			col = 0
		x = startx + col* (sizex + spacex)
		y = starty + row * (sizey + spacey)
		sign.paste(lvlbg,(x,y+sizey-rad))
		card = Image.new("RGBA", (sizex,sizey), (0, 0, 0, 0))
		carddraw = ImageDraw.Draw(card)
		if character.collab:
			card.paste(spbg,(0,0))
		elif character.rarity == 4:
			card.paste(l4bg,(0,0))
		else:
			card.paste(l5bg,(0,0))
		im = getimage(character.icon).resize((sizey,sizey),Image.ANTIALIAS).crop(((sizey - sizex) / 2, 0, (sizey + sizex) / 2, sizey))
		card.paste(im,(0,0),im)
		if character.element != '':
			eleim = eleicons[elementorder(character.element)]
			card.paste(eleim,(2,2),eleim)
		if character.constellation > 0:
			card.paste(conbg,(sizex - 21,2),conbg)
			if character.constellation < 6:
				carddraw.text((sizex - 17, 2),str(character.constellation),(255,255,255),font=confont)
			else:
				carddraw.text((sizex - 17, 2),str(character.constellation),(255,215,0),font=confont)
		details = await client.get_character_details(character.id)
		if True:
			t = 0
			for talent in details.talents:
				if talent.max_level == 10:
					if talent.level == 10:
						carddraw.text((4, 35 + 17 * t),str(talent.level),(0,191,255),font=lvlfont)
					else:
						carddraw.text((4, 35 + 17 * t),str(talent.level),(255,255,255),font=lvlfont)
					t += 1
		sign.paste(card,(x,y),alpha)

		if character.element == '':
			draw.text((x + sizex/2 - 20, y + sizey + 3), 'Lv. ' +  str(character.level),(0,0,0) ,font=lvlfont)
		else:
			draw.text((x + 14, y + sizey + 3), 'Lv. ' +  str(character.level),(0,0,0) ,font=lvlfont)
			sign.paste(flicon,(x + sizex - 44,y + sizey + 1),flicon)
			if character.friendship == 10:
				draw.text((x + sizex - 22, y + sizey + 4), '10',(0,0,0) ,font=flfont)
				flcnt = flcnt + 1
			else:
				draw.text((x + sizex - 22, y + sizey + 3), str(character.friendship),(102,102,255) ,font=lvlfont)
		col = col  + 1

	draw.text((cardx - 122, cardy - 138), f"{user.nickname}  AR {user.level}",(255,255,255) ,font=notefont)
	draw.text((cardx - 122, cardy - 119), f"满好感角色: {flcnt}/{data.stats.characters - 1}",(255,255,255) ,font=notefont)
	draw.text((cardx - 122, cardy - 100), f"活跃天数: {data.stats.days_active}",(255,255,255) ,font=notefont)
	draw.text((cardx - 122, cardy - 81), f"成就达成数: {data.stats.achievements}",(255,255,255) ,font=notefont)
	draw.text((cardx - 122, cardy - 62), f"深境螺旋: {abyss.max_floor} {abyss.total_stars}星",(255,255,255) ,font=notefont)
	draw.text((cardx - 119, cardy - 38), f"UID: {user.uid}",(255,255,255) ,font=notefont)
	from datetime import datetime
	draw.text((cardx - 85, cardy - 20), datetime.now().strftime("%Y/%m/%d") ,font=notefont)
	sign.save("box.png", "PNG")
	sign.show()



asyncio.run(main())
