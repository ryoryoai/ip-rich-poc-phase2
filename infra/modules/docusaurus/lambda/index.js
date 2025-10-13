/**
 * Lambda@Edge function for Cognito authentication
 * Based on cognito-at-edge pattern
 */

const { CognitoJwtVerifier } = require("aws-jwt-verify");
const https = require('https');
const querystring = require('querystring');

// Configuration - hardcoded for Lambda@Edge (no environment variables allowed)
const CONFIG = {
  USER_POOL_ID: '${USER_POOL_ID}',
  CLIENT_ID: '${CLIENT_ID}',
  CLIENT_SECRET: '${CLIENT_SECRET}',
  COGNITO_DOMAIN: '${COGNITO_DOMAIN}',
  REGION: '${REGION}',
  CALLBACK_PATH: '/oauth2/callback',
};

// JWT Verifier
const verifier = CognitoJwtVerifier.create({
  userPoolId: CONFIG.USER_POOL_ID,
  tokenUse: "id",
  clientId: CONFIG.CLIENT_ID,
});

/**
 * Main handler
 */
exports.handler = async (event) => {
  const request = event.Records[0].cf.request;
  const headers = request.headers;
  const uri = request.uri;
  const queryString = request.querystring;

  console.log('Request URI:', uri);
  console.log('Query String:', queryString);

  // OAuth2 callback handler
  if (uri === CONFIG.CALLBACK_PATH) {
    return await handleCallback(request, queryString);
  }

  // Check for authentication
  const cookies = parseCookies(headers.cookie);
  const idToken = cookies[`CognitoIdentityServiceProvider.$${CONFIG.CLIENT_ID}.idToken`];

  if (idToken) {
    try {
      // Verify JWT token
      const payload = await verifier.verify(idToken);
      console.log('Token verified for user:', payload.email);

      // Allow access
      return request;
    } catch (error) {
      console.log('Token verification failed:', error.message);
      // Token invalid, redirect to login
    }
  }

  // No valid token, redirect to Cognito login
  return redirectToLogin(request);
};

/**
 * Handle OAuth2 callback
 */
async function handleCallback(request, queryString) {
  const params = querystring.parse(queryString);
  const code = params.code;

  if (!code) {
    return {
      status: '400',
      statusDescription: 'Bad Request',
      body: 'Missing authorization code',
    };
  }

  try {
    // Exchange code for tokens
    const tokens = await exchangeCodeForTokens(code, request);

    // Set cookies
    const cookieName = `CognitoIdentityServiceProvider.$${CONFIG.CLIENT_ID}`;
    const cookies = [
      `$${cookieName}.idToken=$${tokens.id_token}; Secure; HttpOnly; Path=/; Max-Age=3600`,
      `$${cookieName}.accessToken=$${tokens.access_token}; Secure; HttpOnly; Path=/; Max-Age=3600`,
      `$${cookieName}.refreshToken=$${tokens.refresh_token}; Secure; HttpOnly; Path=/; Max-Age=2592000`,
    ];

    // Redirect to original page or home
    const redirectUri = params.state || '/';

    return {
      status: '302',
      statusDescription: 'Found',
      headers: {
        'location': [{
          key: 'Location',
          value: redirectUri,
        }],
        'set-cookie': cookies.map(cookie => ({
          key: 'Set-Cookie',
          value: cookie,
        })),
      },
    };
  } catch (error) {
    console.error('Token exchange failed:', error);
    return {
      status: '500',
      statusDescription: 'Internal Server Error',
      body: 'Authentication failed',
    };
  }
}

/**
 * Exchange authorization code for tokens
 */
function exchangeCodeForTokens(code, request) {
  return new Promise((resolve, reject) => {
    const domain = request.headers.host[0].value;
    const redirectUri = `https://$${domain}$${CONFIG.CALLBACK_PATH}`;

    const postData = querystring.stringify({
      grant_type: 'authorization_code',
      client_id: CONFIG.CLIENT_ID,
      client_secret: CONFIG.CLIENT_SECRET,
      code: code,
      redirect_uri: redirectUri,
    });

    const options = {
      hostname: `$${CONFIG.COGNITO_DOMAIN}.auth.$${CONFIG.REGION}.amazoncognito.com`,
      port: 443,
      path: '/oauth2/token',
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': postData.length,
      },
    };

    const req = https.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        if (res.statusCode === 200) {
          resolve(JSON.parse(data));
        } else {
          reject(new Error(`Token exchange failed: $${res.statusCode} $${data}`));
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.write(postData);
    req.end();
  });
}

/**
 * Redirect to Cognito login page
 */
function redirectToLogin(request) {
  const domain = request.headers.host[0].value;
  const redirectUri = `https://$${domain}$${CONFIG.CALLBACK_PATH}`;
  const state = request.uri;

  const loginUrl = `https://$${CONFIG.COGNITO_DOMAIN}.auth.$${CONFIG.REGION}.amazoncognito.com/login?` +
    querystring.stringify({
      client_id: CONFIG.CLIENT_ID,
      response_type: 'code',
      scope: 'openid email profile',
      redirect_uri: redirectUri,
      state: state,
    });

  return {
    status: '302',
    statusDescription: 'Found',
    headers: {
      'location': [{
        key: 'Location',
        value: loginUrl,
      }],
      'cache-control': [{
        key: 'Cache-Control',
        value: 'no-cache, no-store, must-revalidate',
      }],
    },
  };
}

/**
 * Parse cookies from headers
 */
function parseCookies(cookieHeaders) {
  const cookies = {};
  if (cookieHeaders) {
    cookieHeaders.forEach((cookieHeader) => {
      const cookie = cookieHeader.value;
      cookie.split(';').forEach((part) => {
        const [key, value] = part.trim().split('=');
        if (key && value) {
          cookies[key] = value;
        }
      });
    });
  }
  return cookies;
}
