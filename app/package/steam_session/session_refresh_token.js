const { EAuthTokenPlatformType, LoginSession } = require('steam-session');

if (process.argv.length <= 2) {
    console.log("Usage: node session_refresh_token.js <refreshToken>");
    process.exit(1);
}

// node session_refresh_token.js <refreshToken>"
const refreshToken = process.argv[2];

(async () => {

    try {
        let session = new LoginSession(EAuthTokenPlatformType.WebBrowser);
        session.refreshToken = refreshToken;

        let webCookies = await session.getWebCookies();
        console.log(`steamID=${session.steamID}`);
        console.log(`refreshToken=${session.refreshToken}`);
        webCookies.forEach(element => {
            console.log(element);
        });
        process.exit(0);
    } catch (ex) {
        console.error(`Login failed: ${ex.message}`);
        process.exit(1);
    }
})();
