from discord.ext import commands
from .utils import utils
import traceback
import datetime
import discord
import sys
class Events():
    def __init__(self,bot):
        self.bot = bot
        self.redis = bot.db.redis

    def Time(self):
        return datetime.datetime.now().strftime("%b/%d/%Y %H:%M:%S")

#############################################################
#    _        _         _                                   #
#   | |      (_)       | |                                  #
#   | |       _   ___  | |_    ___   _ __     ___   _ __    #
#   | |      | | / __| | __|  / _ \ | '_ \   / _ \ | '__|   #
#   | |____  | | \__ \ | |_  |  __/ | | | | |  __/ | |      #
#   |______| |_| |___/  \__|  \___| |_| |_|  \___| |_|      #
#                                                           #
#############################################################

    async def on_server_join(self,server): #IF Bot join server, it will add to record of those.
        print ("\033[96m<EVENT JOIN>: \033[94m {} :({}) -- {}\033[00m".format(self.Time(), server.id, server.name))
        utils.prGreen("\t\t Servers: {}\t\t Members: {}".format(len(self.bot.servers), len(set(self.bot.get_all_members()))))
        await self.redis.hset("Info:Server",str(server.id),str(server.name))
        await self.redis.set("Info:Total Server",len(self.bot.servers))
        await self.redis.set("Info:Total Member",len(set(self.bot.get_all_members())))
        await self.redis.set("{}:Config:CMD_Prefix".format(server.id),"!")
        #Server setting
        await self.redis.hset("{}:Config:Delete_MSG".format(server.id),"core","off")

    async def on_server_remove(self,server): #IF bot left or no longer in that server. It will remove this
        print("\033[91m<EVENT LEFT>:\033[94m[ {} : \033[96m({})\033[92m -- {}\033[00m".format(self.Time(), str(server.id), str(server.name)))
        utils.prGreen("\t\t Severs:{}\t\tMembers:{}".format(len(self.bot.servers), len(set(self.bot.get_all_members()))))
        await self.redis.hdel("Info:Server",server.id)

    async def on_server_update(self,before,after): #If server update name and w/e, just in case, Update those
        print("\033[95m<EVENT Update>:\033[94m {} :\033[96m {} \033[93m | \033[92m({}) -- {}\033[00m".format(self.Time(),after.name,after.id, after))
        if after.icon:
            await self.redis.set("{}:Icon".format(after.id),after.icon)
        await self.redis.hset("Info:Server",str(after.id),str(after))

    async def on_member_join(self,member):
        print("\033[98m<Event Member Join>:\033[94m {} :\033[96m {} ||| \033[93m ({})\033[92m  -- {} ||| {}\033[00m".format(self.Time(), member.server.name, member.server.id, member.name, member.id))
        await self.redis.set("Info:Total Member",len(set(self.bot.get_all_members())))

    async def on_member_remove(self,member):
        print("\033[93m<Event Member Left>:\033[94m {}:\033[96m {} ||| \033[93m ({})\033[92m -- {} ||| {}\033[00m".format(self.Time(), member.server.name, member.server.id, member.name, member.id))
        await self.redis.set("Info:Total Member",len(set(self.bot.get_all_members())))

    async def on_member_update(self,before,after):
        check = await self.redis.get("Member_Update:{}:check".format(after.id))
        if check: #If it true, return, it haven't cool down yet
            return
        if before.avatar != after.avatar:
            if after.avatar is None:
                return
            print("\033[97m<Event Member Update Avatar>:\033[94m {} :\033[92m {} ||| {}\033[00m".format(self.Time(), after.name, after.id))
            await self.redis.hset("Info:Icon",after.id,after.avatar)
        if before.name != after.name:
            print("\033[97m<Event Member Update Name>: \033[94m {}:\033[93m Before : {} |||\033[92m After : {} ||| {}\033[00m".format(self.Time(),before.name,after.name, after.id))
            await self.redis.hset("Info:Name",after.id,after.name)
        await self.redis.set("Member_Update:{}:check".format(after.id),'cooldown',expire=15) #To stop multi update

    async def on_command(self,command,ctx):
        if ctx.message.channel.is_private:
            return
        print("\033[96m<Event Command>\033[94m {0}:\033[96m {1.server.name} ||| \033[93m {1.author} ||| \033[94m ({1.author.id})\033[92m ||| {1.clean_content}\033[00m".format(self.Time(), ctx.message))

    async def on_message(self,msg):
            if self.bot.user.id == msg.author.id:
                if msg.channel.is_private is False:
                    try:
                        if self.bot.log_config.get(msg.server.id):
                            if msg.channel.id in self.bot.log_config[msg.server.id]['channel']:
                                return
                    except:
                        pass
                if msg.channel.is_private:
                    utils.prCyan("PRIVATE")
                    utils.prGreen("<Event Send> {} : {} |||{}".format(self.Time(), msg.author.name, msg.clean_content))
                else:
                    utils.prGreen("<Event Send> {} : {} ||| {} ||| ({}) ||| {}".format(self.Time(), msg.author.name,msg.server.name,msg.server.id, msg.clean_content))

    async def on_command_completion(self,command,ctx):
        if command.cog_name is None:
            return
        if ctx.message.channel.is_private:
            return
        try:
            print(command.cog_name)
            check = await self.bot.db.redis.hgetall("{}:Config:Delete_MSG".format(ctx.message.server.id))
            if check.get(command.cog_name.lower()) == "on":
                await self.bot.delete_message(ctx.message)
            await self.redis.hincrby("{0.server.id}:Total_Command:{0.author.id}".format(ctx.message),ctx.invoked_with, increment=1)
            await self.redis.hincrby("Info:Total_Command", ctx.invoked_with, increment=1)
            await self.redis.hincrby("{0.server.id}:Total_Command:User:{0.author.id}".format(ctx.message),ctx.invoked_with, increment=1)
        except:
            utils.prRed("Failed to delete user command - {0.name}  - {0.id}\n".format(ctx.message.server))
            utils.prRed(traceback.format_exc())

    async def send_cmd_help(self,ctx):
        if ctx.invoked_subcommand:
            pages = self.bot.formatter.format_help_for(ctx,ctx.invoked_subcommand)
            for page in pages:
                await self.bot.send_message(ctx.message.channel, page.replace("\n","fix\n",1))
        else:
            pages = self.bot.formatter.format_help_for(ctx,ctx.command)
            for page in pages:
                await self.bot.send_message(ctx.message.channel,page.replace("\n","fix\n",1))

    async def on_command_error(self,error,ctx):
        if self.bot.user.id == "181503794532581376":
            print(error)
        if isinstance(error, commands.MissingRequiredArgument):
            await self.send_cmd_help(ctx)
        elif isinstance(error,commands.BadArgument):
            await self.send_cmd_help(ctx)
        elif isinstance(error, commands.CommandInvokeError):
            errors = traceback.format_exception(type(error), error, error.__traceback__)
            Current_Time = datetime.datetime.utcnow().strftime("%b/%d/%Y %H:%M:%S UTC")
            utils.prRed(Current_Time)
            utils.prRed("Error!")
            traceback.print_exception(type(error), error, error.__traceback__)
            cog_error =  '```fix\nCogs:{}\tCommand:{}\tAuthor:{}\n{}\nError:\n{}```'.format(ctx.command.cog_name,ctx.command,ctx.message.author,ctx.message.clean_content,error)
            user=discord.utils.get(self.bot.get_all_members(),id="105853969175212032")
            await self.bot.send_message(user, "```py\n{}```\n{}\n```py\n{}\n```".format(Current_Time + "\n"+ "ERROR!",cog_error,"".join(errors)))
            await self.bot.send_message(ctx.message.channel,"There is problem, I have send report to creator,\n hopefully it will fixed in time?,Maybe you did it wrongly.")

def setup(bot):
    bot.add_cog(Events(bot))
