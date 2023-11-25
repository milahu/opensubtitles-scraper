https://news.ycombinator.com/item?id=38241080

<blockquote>

keepamovin 2023-11-12

I actually really like GitHub actions, I read the article and while I get some of the concerns, others I don't understand. In any case the author's situation doesn't apply to me, and I wanted to share something I really liked about GHA.
So, I recently figured out a way to host a remote browser on them by using an Ngrok tunnel. It's really cool to see BrowserBox running from inside a GitHub action container. I literally couldn't believe it actually worked when I first figured it out!

I was so excited. It started as just this tech prototype in my mind (could this be possible? Probably not but I Feel like it could be). And to see it actually achieved so cool! :)

It has made CI integration testing SO much easier and more repeatable. I love that it can just run it up on Ubuntu and I can verify.

Anyhow, I thought this was so cool, and such a useful way for people to either just get started with BrowserBox trying it out, or even run a quick little VPN-like/proxy browser from another region. I've even logged into HN from it on the sly. I liked this whoel concept so much, that I even wrote an action that integrates with issues to make the process as easy as possible for people.

Basically you can just clone or fork the repo: https://github.com/BrowserBox/BrowserBox and then open an issue and pick the template that is like "Make VPN". The login link will get published in the repo. The link is not private (unless you make your fork or template private) and there's a bit of setup with your ngrok API key (free is OK) but the issue conversation automatically guides you through all that.

I thought this was so cool (free server time, actually working app), that I even created another version that uses MS Edge under the hood instead of Chrome in the original, just to show how easy it is: https://github.com/MSEdgeLord/EdgeLord

Just a niggle is that the other services we normally have (secure doc viewer, audio, remote devtools) do not work as ngrok only maps 1 port. I could use an ngrok config file I think to fix that but somehow, easy as that is, I have not gotten around to it! Another niggle is I noticed the auto-tab opening used in the GHA demo seems a little funky lately, and you may need to manually reload or resize them to un-wonkify it. Probably a little regression!

Anyway! :)

</blockquote>

<blockquote>
	
PLG88 2023-11-12

Super cool. Have you considered using alternative technology that allows more mapping than 1 port, e.g., open source OpenZiti? This is an example of embedding their SDKs into a webhook action to connect to a server in a completely private network - https://netfoundry.io/this-is-the-way-invisible-jenkins/

</blockquote>

https://github.com/BrowserBox/BrowserBox#github-actions-method

> github action to create a BrowserBox Tor Hidden Service

> Create a private ephemeral Web Proxy hosted on your GitHub Actions

> don't do anything abusive with this, remember you are browsing the web from inside GitHub's infrastructure (actions runners), so treat them with respect!

## mxschmitt/action-tmate

https://github.com/mxschmitt/action-tmate

Debug your GitHub Actions via SSH by using tmate to get access to the runner system itself.
