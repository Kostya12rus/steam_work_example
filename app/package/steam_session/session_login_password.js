const { EAuthSessionGuardType, EAuthTokenPlatformType, LoginSession } = require('steam-session');

if (process.argv.length <= 2) {
    console.log("Usage: node session_login_password.js <login>:<password>:<code>");
    process.exit(1);
}

// node session_login_password.js <login>:<password>:<code>"
const account = process.argv[2].split(':');
const [accountName, password, code] = account;

(async () => {
    let session = new LoginSession(EAuthTokenPlatformType.WebBrowser);

    try {
        let startResult = await session.startWithCredentials({
            accountName,
            password,
        });

        console.log(`actionRequired: ${startResult.actionRequired}`);
        for (const action of startResult.validActions) {
            console.log(action.type, action.detail);
        }

        if (code && startResult.actionRequired && startResult.validActions.some(
            action => action.type === EAuthSessionGuardType.DeviceCode)) {
            await session.submitSteamGuardCode(code);
        } else if (startResult.actionRequired && startResult.validActions.some(
            action => action.type === EAuthSessionGuardType.DeviceConfirmation)) {
            console.log('DeviceConfirmation');
        } else if (startResult.actionRequired && startResult.validActions.some(
            action => action.type === EAuthSessionGuardType.EmailConfirmation)) {
            console.log('EmailConfirmation');
        } else if (startResult.actionRequired) {
            console.log(`actionRequired: ${startResult.actionRequired}, validActions: ${startResult.validActions}`);
            throw new Error('Login action is required, but we don\'t know how to handle it');
        }
    } catch (ex) {
        console.log(`Login failed: ${ex.message}`);
        process.exit(1);
    }

    session.on('authenticated', async () => {
        console.log(`accountName=${session.accountName}`);
        console.log(`steamID=${session.steamID}`);
        console.log(`refreshToken=${session.refreshToken}`);
        let webCookies = await session.getWebCookies();
        webCookies.forEach(element => {
            console.log(element);
        });
        process.exit(0);  // Successful exit
    });

    session.on('timeout', () => {
        console.log('This login attempt has timed out.');
        process.exit(1);
    });

    session.on('error', (err) => {
        console.log(`An error occurred: ${err.message}`);
        process.exit(1);
    });
})();
