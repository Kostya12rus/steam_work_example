const { EAuthSessionGuardType, EAuthTokenPlatformType, LoginSession } = require('steam-session');
// node session_qrcode.js

(async () => {
    let session = new LoginSession(EAuthTokenPlatformType.WebBrowser);
    const qr_login = session.startWithQR();
    console.log((await qr_login).qrChallengeUrl)

    session.on('authenticated', async () => {
        console.log(`accountName=${session.accountName}`);
        console.log(`steamID=${session.steamID}`);
        console.log(`refreshToken=${session.refreshToken}`);
        let webCookies = await session.getWebCookies();
        webCookies.forEach(element => {
            console.log(element);
        });
        process.exit(0);
    });

    session.on('timeout', () => {
        console.error('This login attempt has timed out.');
        process.exit(1);
    });

    session.on('error', (err) => {
        console.error(`An error occurred: ${err.message}`);
        process.exit(1);
    });
})();