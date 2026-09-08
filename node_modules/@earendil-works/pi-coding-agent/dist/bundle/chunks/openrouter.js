import { createRequire as __piCreateRequire } from "node:module"; const require = __piCreateRequire(import.meta.url);
var __require=(x=>typeof require<"u"?require:typeof Proxy<"u"?new Proxy(x,{get:(a,b)=>(typeof require<"u"?require:a)[b]}):x)(function(x){if(typeof require<"u")return require.apply(this,arguments);throw Error('Dynamic require of "'+x+'" is not supported')});import{createServer}from"node:http";var procEnvCache=null;function getBunSandboxEnvValue(name){if(!(typeof process>"u"||!process.versions?.bun||Object.keys(process.env).length>0)){if(procEnvCache===null){procEnvCache=new Map;try{let{readFileSync}=__require("node:fs"),data=readFileSync("/proc/self/environ","utf-8");for(let entry of data.split("\0")){let idx=entry.indexOf("=");idx>0&&procEnvCache.set(entry.slice(0,idx),entry.slice(idx+1))}}catch{}}return procEnvCache.get(name)}}function getProviderEnvValue(name,env){return env?.[name]||(typeof process<"u"?process.env[name]:void 0)||getBunSandboxEnvValue(name)||void 0}var LOGO_SVG='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" aria-hidden="true"><path fill="#fff" fill-rule="evenodd" d="M165.29 165.29 H517.36 V400 H400 V517.36 H282.65 V634.72 H165.29 Z M282.65 282.65 V400 H400 V282.65 Z"/><path fill="#fff" d="M517.36 400 H634.72 V634.72 H517.36 Z"/></svg>';function escapeHtml(value){return value.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}function renderPage(options){let title=escapeHtml(options.title),heading=escapeHtml(options.heading),message=escapeHtml(options.message),details=options.details?escapeHtml(options.details):void 0;return`<!doctype html>
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
</html>`}function oauthSuccessHtml(message){return renderPage({title:"Authentication successful",heading:"Authentication successful",message})}function oauthErrorHtml(message,details){return renderPage({title:"Authentication failed",heading:"Authentication failed",message,details})}function base64urlEncode(bytes){let binary="";for(let byte of bytes)binary+=String.fromCharCode(byte);return btoa(binary).replace(/\+/g,"-").replace(/\//g,"_").replace(/=/g,"")}async function generatePKCE(){let verifierBytes=new Uint8Array(32);crypto.getRandomValues(verifierBytes);let verifier=base64urlEncode(verifierBytes),data=new TextEncoder().encode(verifier),hashBuffer=await crypto.subtle.digest("SHA-256",data),challenge=base64urlEncode(new Uint8Array(hashBuffer));return{verifier,challenge}}var AUTHORIZE_URL="https://openrouter.ai/auth",TOKEN_URL="https://openrouter.ai/api/v1/auth/keys",LOGIN_TIMEOUT_MS=300*1e3,TOKEN_EXCHANGE_TIMEOUT_MS=3e4;function getCallbackHost(){return getProviderEnvValue("PI_OAUTH_CALLBACK_HOST")||"127.0.0.1"}function sendHtml(response,status,html){response.statusCode=status,response.setHeader("content-type","text/html; charset=utf-8"),response.setHeader("cache-control","no-store"),response.end(html)}function parseAuthorizationInput(input){let value=input.trim();if(value){try{return new URL(value).searchParams.get("code")??void 0}catch{}return value.includes("code=")?new URLSearchParams(value).get("code")??void 0:value}}function errorDetail(body){if(typeof body.error_description=="string")return body.error_description;if(typeof body.message=="string")return body.message;if(typeof body.error=="string")return body.error;if(body.error&&typeof body.error=="object"&&!Array.isArray(body.error)){let message=body.error.message;if(typeof message=="string")return message}}async function exchangeAuthorizationCode(code,verifier,signal){if(signal.aborted)throw new Error("Login cancelled");let controller=new AbortController,onAbort=()=>controller.abort(signal.reason);signal.addEventListener("abort",onAbort,{once:!0});let timeout=setTimeout(()=>controller.abort(new Error("OpenRouter OAuth token exchange timed out")),TOKEN_EXCHANGE_TIMEOUT_MS),response,body={};try{response=await fetch(TOKEN_URL,{method:"POST",headers:{accept:"application/json","content-type":"application/json"},body:JSON.stringify({code,code_verifier:verifier,code_challenge_method:"S256"}),signal:controller.signal});try{let parsed=await response.json();parsed&&typeof parsed=="object"&&!Array.isArray(parsed)&&(body=parsed)}catch{if(response.ok)throw new Error("OpenRouter OAuth returned invalid JSON")}}catch(error){throw signal.aborted?new Error("Login cancelled"):controller.signal.aborted?new Error("OpenRouter OAuth token exchange timed out"):error}finally{clearTimeout(timeout),signal.removeEventListener("abort",onAbort)}if(!response.ok){let detail=errorDetail(body);throw new Error(`OpenRouter OAuth key exchange failed (HTTP ${response.status})${detail?`: ${detail}`:""}`)}if(typeof body.key!="string"||body.key.length===0)throw new Error('OpenRouter OAuth response carries no "key"');return{type:"oauth",access:body.key,refresh:"",expires:Number.MAX_SAFE_INTEGER}}async function startCallbackServer(callbackPath,verifier,signal){if(signal.aborted)throw new Error("Login cancelled");let callbackHost=getCallbackHost(),resolveCredential=()=>{},rejectCredential=()=>{},credential=new Promise((resolve,reject)=>{resolveCredential=resolve,rejectCredential=reject}),server,claimed=!1,settled=!1,timeout,onAbort,close=()=>{timeout&&clearTimeout(timeout),onAbort&&signal.removeEventListener("abort",onAbort),server.close()},finish=result=>{settled||(settled=!0,close(),"credential"in result?resolveCredential(result.credential):rejectCredential(result.error))};if(server=createServer((request,response)=>{(async()=>{let requestUrl=new URL(request.url??"/",`http://${callbackHost}`);if(request.method!=="GET"||requestUrl.pathname!==callbackPath){sendHtml(response,404,oauthErrorHtml("OAuth callback route not found."));return}if(claimed||settled){sendHtml(response,409,oauthErrorHtml("This OAuth callback has already been used."));return}let oauthError=requestUrl.searchParams.get("error");if(oauthError){let description=requestUrl.searchParams.get("error_description")??oauthError;sendHtml(response,400,oauthErrorHtml("OpenRouter authorization was denied.",description)),finish({error:new Error(`OpenRouter authorization failed: ${description}`)});return}let code=requestUrl.searchParams.get("code");if(!code){sendHtml(response,400,oauthErrorHtml("OpenRouter returned no authorization code."));return}claimed=!0;try{let result=await exchangeAuthorizationCode(code,verifier,signal);sendHtml(response,200,oauthSuccessHtml("Signed in to OpenRouter. You may now close this page.")),finish({credential:result})}catch(error){let message=error instanceof Error?error.message:"Unknown token exchange error";sendHtml(response,502,oauthErrorHtml("OpenRouter key exchange failed.",message)),finish({error:error instanceof Error?error:new Error(message)})}})()}),await new Promise((resolve,reject)=>{server.once("error",reject),server.listen(0,callbackHost,()=>{server.removeListener("error",reject),resolve()})}),server.on("error",error=>finish({error})),onAbort=()=>finish({error:new Error("Login cancelled")}),signal.addEventListener("abort",onAbort,{once:!0}),signal.aborted)throw close(),new Error("Login cancelled");timeout=setTimeout(()=>finish({error:new Error("OpenRouter OAuth login timed out")}),LOGIN_TIMEOUT_MS);let address=server.address();if(!address||typeof address=="string")throw close(),new Error("Could not determine the OpenRouter OAuth callback port");return{callbackUrl:`http://${callbackHost}:${address.port}${callbackPath}`,close,cancelWait:()=>{claimed||finish({credential:null})},waitForCredential:()=>credential}}async function loginOpenRouter(interaction){let{verifier,challenge}=await generatePKCE(),callbackPath=`/oauth/callback/${crypto.randomUUID()}`,callback=await startCallbackServer(callbackPath,verifier,interaction.signal),manualAbort=new AbortController,manualInput,manualError;try{let authorizeUrl=new URL(AUTHORIZE_URL);authorizeUrl.search=new URLSearchParams({callback_url:callback.callbackUrl,code_challenge:challenge,code_challenge_method:"S256"}).toString(),interaction.notify({type:"progress",message:`Listening for OpenRouter OAuth callback on ${callback.callbackUrl}`}),interaction.notify({type:"auth_url",url:authorizeUrl.toString(),instructions:"Complete sign-in in your browser. If the browser is on another machine, paste the final redirect URL here."});let manualPromise=interaction.prompt({type:"manual_code",message:"Complete sign-in in your browser, or paste the authorization code / redirect URL here:",placeholder:callback.callbackUrl,signal:manualAbort.signal}).then(input=>{manualInput=input,callback.cancelWait()}).catch(error=>{manualError=error instanceof Error?error:new Error(String(error)),callback.cancelWait()}),credential=await callback.waitForCredential();if(manualError)throw manualError;if(credential)return credential;if(await manualPromise,manualError)throw manualError;let code=manualInput?parseAuthorizationInput(manualInput):void 0;if(!code)throw new Error("Missing authorization code");return interaction.notify({type:"progress",message:"Exchanging authorization code for an API key..."}),await exchangeAuthorizationCode(code,verifier,interaction.signal)}finally{manualAbort.abort(),callback.close()}}var openRouterOAuth={name:"OpenRouter OAuth",loginLabel:"Sign in with OpenRouter",login:loginOpenRouter,async refresh(credential,_signal){return credential},async toAuth(credential){return{apiKey:credential.access}}};export{openRouterOAuth};
