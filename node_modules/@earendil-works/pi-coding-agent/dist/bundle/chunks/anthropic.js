import { createRequire as __piCreateRequire } from "node:module"; const require = __piCreateRequire(import.meta.url);
var __require=(x=>typeof require<"u"?require:typeof Proxy<"u"?new Proxy(x,{get:(a,b)=>(typeof require<"u"?require:a)[b]}):x)(function(x){if(typeof require<"u")return require.apply(this,arguments);throw Error('Dynamic require of "'+x+'" is not supported')});var procEnvCache=null;function getBunSandboxEnvValue(name){if(!(typeof process>"u"||!process.versions?.bun||Object.keys(process.env).length>0)){if(procEnvCache===null){procEnvCache=new Map;try{let{readFileSync}=__require("node:fs"),data=readFileSync("/proc/self/environ","utf-8");for(let entry of data.split("\0")){let idx=entry.indexOf("=");idx>0&&procEnvCache.set(entry.slice(0,idx),entry.slice(idx+1))}}catch{}}return procEnvCache.get(name)}}function getProviderEnvValue(name,env){return env?.[name]||(typeof process<"u"?process.env[name]:void 0)||getBunSandboxEnvValue(name)||void 0}var LOGO_SVG='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" aria-hidden="true"><path fill="#fff" fill-rule="evenodd" d="M165.29 165.29 H517.36 V400 H400 V517.36 H282.65 V634.72 H165.29 Z M282.65 282.65 V400 H400 V282.65 Z"/><path fill="#fff" d="M517.36 400 H634.72 V634.72 H517.36 Z"/></svg>';function escapeHtml(value){return value.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}function renderPage(options){let title=escapeHtml(options.title),heading=escapeHtml(options.heading),message=escapeHtml(options.message),details=options.details?escapeHtml(options.details):void 0;return`<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${title}</title>
  <style>
    :root {
      --text: #fafafa;
      --text-dim: #a1a1aa;
      --page-bg: #09090b;
      --font-sans: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }
    * { box-sizing: border-box; }
    html { color-scheme: dark; }
    body {
      margin: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
      background: var(--page-bg);
      color: var(--text);
      font-family: var(--font-sans);
      text-align: center;
    }
    main {
      width: 100%;
      max-width: 560px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }
    .logo {
      width: 72px;
      height: 72px;
      display: block;
      margin-bottom: 24px;
    }
    h1 {
      margin: 0 0 10px;
      font-size: 28px;
      line-height: 1.15;
      font-weight: 650;
      color: var(--text);
    }
    p {
      margin: 0;
      line-height: 1.7;
      color: var(--text-dim);
      font-size: 15px;
    }
    .details {
      margin-top: 16px;
      font-family: var(--font-mono);
      font-size: 13px;
      color: var(--text-dim);
      white-space: pre-wrap;
      word-break: break-word;
    }
  </style>
</head>
<body>
  <main>
    <div class="logo">${LOGO_SVG}</div>
    <h1>${heading}</h1>
    <p>${message}</p>
    ${details?`<div class="details">${details}</div>`:""}
  </main>
</body>
</html>`}function oauthSuccessHtml(message){return renderPage({title:"Authentication successful",heading:"Authentication successful",message})}function oauthErrorHtml(message,details){return renderPage({title:"Authentication failed",heading:"Authentication failed",message,details})}function base64urlEncode(bytes){let binary="";for(let byte of bytes)binary+=String.fromCharCode(byte);return btoa(binary).replace(/\+/g,"-").replace(/\//g,"_").replace(/=/g,"")}async function generatePKCE(){let verifierBytes=new Uint8Array(32);crypto.getRandomValues(verifierBytes);let verifier=base64urlEncode(verifierBytes),data=new TextEncoder().encode(verifier),hashBuffer=await crypto.subtle.digest("SHA-256",data),challenge=base64urlEncode(new Uint8Array(hashBuffer));return{verifier,challenge}}var nodeApis=null,nodeApisPromise=null,decode=s=>atob(s),CLIENT_ID=decode("OWQxYzI1MGEtZTYxYi00NGQ5LTg4ZWQtNTk0NGQxOTYyZjVl"),AUTHORIZE_URL="https://claude.ai/oauth/authorize",TOKEN_URL="https://platform.claude.com/v1/oauth/token",CALLBACK_HOST=getProviderEnvValue("PI_OAUTH_CALLBACK_HOST")||"127.0.0.1",CALLBACK_PORT=53692,CALLBACK_PATH="/callback",REDIRECT_URI=`http://localhost:${CALLBACK_PORT}${CALLBACK_PATH}`,SCOPES="org:create_api_key user:profile user:inference user:sessions:claude_code user:mcp_servers user:file_upload";async function getNodeApis(){if(nodeApis)return nodeApis;if(!nodeApisPromise){if(typeof process>"u"||!process.versions?.node&&!process.versions?.bun)throw new Error("Anthropic OAuth is only available in Node.js environments");nodeApisPromise=import("node:http").then(httpModule=>({createServer:httpModule.createServer}))}return nodeApis=await nodeApisPromise,nodeApis}function parseAuthorizationInput(input){let value=input.trim();if(!value)return{};try{let url=new URL(value);return{code:url.searchParams.get("code")??void 0,state:url.searchParams.get("state")??void 0}}catch{}if(value.includes("#")){let[code,state]=value.split("#",2);return{code,state}}if(value.includes("code=")){let params=new URLSearchParams(value);return{code:params.get("code")??void 0,state:params.get("state")??void 0}}return{code:value}}function formatErrorDetails(error){if(error instanceof Error){let details=[`${error.name}: ${error.message}`],errorWithCode=error;return errorWithCode.code&&details.push(`code=${errorWithCode.code}`),typeof errorWithCode.errno<"u"&&details.push(`errno=${String(errorWithCode.errno)}`),typeof error.cause<"u"&&details.push(`cause=${formatErrorDetails(error.cause)}`),error.stack&&details.push(`stack=${error.stack}`),details.join("; ")}return String(error)}async function startCallbackServer(expectedState){let{createServer}=await getNodeApis();return new Promise((resolve,reject)=>{let settleWait,waitForCodePromise=new Promise(resolveWait=>{let settled=!1;settleWait=value=>{settled||(settled=!0,resolveWait(value))}}),server=createServer((req,res)=>{try{let url=new URL(req.url||"","http://localhost");if(url.pathname!==CALLBACK_PATH){res.writeHead(404,{"Content-Type":"text/html; charset=utf-8"}),res.end(oauthErrorHtml("Callback route not found."));return}let code=url.searchParams.get("code"),state=url.searchParams.get("state"),error=url.searchParams.get("error");if(error){res.writeHead(400,{"Content-Type":"text/html; charset=utf-8"}),res.end(oauthErrorHtml("Anthropic authentication did not complete.",`Error: ${error}`));return}if(!code||!state){res.writeHead(400,{"Content-Type":"text/html; charset=utf-8"}),res.end(oauthErrorHtml("Missing code or state parameter."));return}if(state!==expectedState){res.writeHead(400,{"Content-Type":"text/html; charset=utf-8"}),res.end(oauthErrorHtml("State mismatch."));return}res.writeHead(200,{"Content-Type":"text/html; charset=utf-8"}),res.end(oauthSuccessHtml("Anthropic authentication completed. You can close this window.")),settleWait?.({code,state})}catch{res.writeHead(500,{"Content-Type":"text/plain; charset=utf-8"}),res.end("Internal error")}});server.on("error",err=>{reject(err)}),server.listen(CALLBACK_PORT,CALLBACK_HOST,()=>{resolve({server,redirectUri:REDIRECT_URI,cancelWait:()=>{settleWait?.(null)},waitForCode:()=>waitForCodePromise})})})}async function postJson(url,body,signal){let response=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json",Accept:"application/json"},body:JSON.stringify(body),signal:AbortSignal.any([signal,AbortSignal.timeout(3e4)])}),responseBody=await response.text();if(!response.ok)throw new Error(`HTTP request failed. status=${response.status}; url=${url}; body=${responseBody}`);return responseBody}async function exchangeAuthorizationCode(code,state,verifier,redirectUri,signal){let responseBody;try{responseBody=await postJson(TOKEN_URL,{grant_type:"authorization_code",client_id:CLIENT_ID,code,state,redirect_uri:redirectUri,code_verifier:verifier},signal)}catch(error){throw new Error(`Token exchange request failed. url=${TOKEN_URL}; redirect_uri=${redirectUri}; response_type=authorization_code; details=${formatErrorDetails(error)}`)}let tokenData;try{tokenData=JSON.parse(responseBody)}catch(error){throw new Error(`Token exchange returned invalid JSON. url=${TOKEN_URL}; body=${responseBody}; details=${formatErrorDetails(error)}`)}return{type:"oauth",refresh:tokenData.refresh_token,access:tokenData.access_token,expires:Date.now()+tokenData.expires_in*1e3-300*1e3}}async function loginAnthropic(interaction){let{verifier,challenge}=await generatePKCE(),server=await startCallbackServer(verifier),manualAbort=new AbortController,onAbort=()=>server.cancelWait();interaction.signal.addEventListener("abort",onAbort,{once:!0}),interaction.signal.aborted&&onAbort();let code,state,manualInput,manualError;try{let authParams=new URLSearchParams({code:"true",client_id:CLIENT_ID,response_type:"code",redirect_uri:REDIRECT_URI,scope:SCOPES,code_challenge:challenge,code_challenge_method:"S256",state:verifier});interaction.notify({type:"auth_url",url:`${AUTHORIZE_URL}?${authParams.toString()}`,instructions:"Complete login in your browser. If the browser is on another machine, paste the final redirect URL here."});let manualPromise=interaction.prompt({type:"manual_code",message:"Complete login in your browser, or paste the authorization code / redirect URL here:",placeholder:REDIRECT_URI,signal:manualAbort.signal}).then(input=>{manualInput=input,server.cancelWait()}).catch(error=>{manualError=error instanceof Error?error:new Error(String(error)),server.cancelWait()}),result=await server.waitForCode();if(manualError)throw manualError;if(result?.code)code=result.code,state=result.state;else if(manualInput){let parsed=parseAuthorizationInput(manualInput);if(parsed.state&&parsed.state!==verifier)throw new Error("OAuth state mismatch");code=parsed.code,state=parsed.state??verifier}if(!code){if(await manualPromise,manualError)throw manualError;if(manualInput){let parsed=parseAuthorizationInput(manualInput);if(parsed.state&&parsed.state!==verifier)throw new Error("OAuth state mismatch");code=parsed.code,state=parsed.state??verifier}}if(!code)throw new Error("Missing authorization code");if(!state)throw new Error("Missing OAuth state");return interaction.notify({type:"progress",message:"Exchanging authorization code for tokens..."}),exchangeAuthorizationCode(code,state,verifier,REDIRECT_URI,interaction.signal)}finally{interaction.signal.removeEventListener("abort",onAbort),manualAbort.abort(),server.server.close()}}async function refreshAnthropicToken(refreshToken,signal){let responseBody;try{responseBody=await postJson(TOKEN_URL,{grant_type:"refresh_token",client_id:CLIENT_ID,refresh_token:refreshToken},signal)}catch(error){throw new Error(`Anthropic token refresh request failed. url=${TOKEN_URL}; details=${formatErrorDetails(error)}`)}let data;try{data=JSON.parse(responseBody)}catch(error){throw new Error(`Anthropic token refresh returned invalid JSON. url=${TOKEN_URL}; body=${responseBody}; details=${formatErrorDetails(error)}`)}return{type:"oauth",refresh:data.refresh_token,access:data.access_token,expires:Date.now()+data.expires_in*1e3-300*1e3}}var anthropicOAuth={name:"Anthropic (Claude Pro/Max)",isSubscription:!0,login:loginAnthropic,refresh:(credential,signal)=>refreshAnthropicToken(credential.refresh,signal),async toAuth(credential){return{apiKey:credential.access}}};export{anthropicOAuth};
