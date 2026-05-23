import os
import discord
from discord.ext import commands
import aiohttp
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

CITIES = {
    "ရန်ကုန်": {"lat": 16.84, "lon": 96.16},
    "မန္တလေး": {"lat": 21.95, "lon": 96.08},
    "နေပြည်တော်": {"lat": 19.74, "lon": 96.11},
    "တောင်ကြီး": {"lat": 20.78, "lon": 97.03},
    "လားရှိုး": {"lat": 22.93, "lon": 97.75}
}

class WeatherDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=city, description=f"{city}မြို့၏ မိုးလေဝသကို ကြည့်မည်")
            for city in CITIES.keys()
        ]
        super().__init__(placeholder="မိုးလေဝသကြည့်မည့် မြို့ကို ရွေးချယ်ပါ...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_city = self.values[0]
        coords = CITIES[selected_city]
        await interaction.response.defer()
        
        async with aiohttp.ClientSession() as session:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&hourly=temperature_2m,precipitation_probability&current=temperature_2m&timezone=Asia/Yangon&forecast_days=1"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    current_temp = data['current']['temperature_2m']
                    times = data['hourly']['time']
                    probs = data['hourly']['precipitation_probability']
                    
                    rain_hours = []
                    for i in range(len(times)):
                        if probs[i] >= 30:
                            time_str = times[i].split("T")[1]
                            rain_hours.append(f"⏰ **{time_str} နာရီ** မှာ မိုးရွာနိုင်ခြေ {probs[i]}%")
                    
                    if not rain_hours:
                        rain_msg = "✨ ဒီနေ့ မိုးရွာရန် အကြောင်းမရှိပါ။ ရာသီဥတု သာယာပါလိမ့်မယ်။"
                    else:
                        rain_msg = "\n".join(rain_hours)
                    
                    # --------------------------------------------------
                    # 🌟 ဤနေရာတွင် ရိုးရိုးစာသားအစား Virtual Embed Card ဆောက်ထားပါသည်
                    # --------------------------------------------------
                    embed = discord.Embed(
                        title=f"📍 {selected_city}မြို့ မိုးလေဝသ အခြေအနေ",
                        description="ယနေ့အတွက် ခန့်မှန်းချက် အချက်အလက်များ",
                        color=discord.Color.blue() # ကတ်ပြား၏ ဘေးဘောင်အရောင် (အပြာရောင်)
                    )
                    
                    # ကတ်ပြားထဲက အကွက်လေးများ (Fields)
                    embed.add_field(name="🌡️ လက်ရှိအပူချိန်", value=f"**{current_temp} °C**", inline=False)
                    embed.add_field(name="🌧️ မိုးရွာမည့် အချိန်ဇယား", value=rain_msg, inline=False)
                    
                    # ကတ်ပြားအောက်ခြေ Footer နှင့် အလှပြပုံရိပ်
                    embed.set_footer(text="Open-Meteo API မှ ဒေတာများကို ရယူထားပါသည်။")
                    embed.set_thumbnail(url="https://i.imgur.com/w996Y7G.png") # မိုးလေဝသ အလှပြ Icon (ပြောင်းလဲနိုင်သည်)
                    
                    # စာသားအစား ဆောက်ထားတဲ့ Embed Card ကို ပို့ခိုင်းလိုက်တာပါ
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send("❌ မိုးလေဝသ ဒေတာ ယူရတာ အဆင်မပြေဖြစ်သွားပါတယ်။")

class WeatherView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(WeatherDropdown())

@bot.event
async def on_ready():
    print(f"{bot.user.name} အလုပ်လုပ်ဖို့ အဆင်သင့်ဖြစ်ပါပြီ!")

@bot.command()
async def weather(commands_ctx):
    await commands_ctx.send("ဘယ်မြို့ရဲ့ မိုးလေဝသ အခြေအနေကို သိချင်ပါသလဲခင်ဗျာ။ တည်နေရာကို Confirm ပေးပါ -", view=WeatherView())

# Render ရဲ့ Port Scan ကို ကျော်ဖြတ်ဖို့ ဟန်ဆောင် ဆာဗာဆောက်ခြင်း
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_health_check():
    port = int(os.getenv("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_check, daemon=True).start()
    
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN မတွေ့ရှိပါ။")
