// import * as CodeMirror from "./CodeMirror";
// import {getCookie, setCookie} from "./cookie";


window.addEventListener('load', function(){
	console.log("Compiler loaded");
	const compilatorSocket = new WebSocket(
		(location.protocol === 'https:' ? 'wss://' : 'ws://') +
		window.location.host + '/ws/compile/'
	);
	//@ts-ignore
	const compileButton  : HTMLButtonElement = document.getElementById('compileButton');//@ts-ignore
	const SaveButton     : HTMLButtonElement = document.getElementById('SaveButton');//@ts-ignore
	const editor: HTMLTextAreaElement = document.getElementById('code_editor');//@ts-ignore
	const autosave: HTMLInputElement = document.getElementById('autosave');//@ts-ignore
	const code_editor = CodeMirror.fromTextArea(editor, {
		lineNumbers: true,//@ts-ignore
		mode: { name: "clike", mode: "csharp" },
		theme: 'material-darker',
		tabSize: 4,
		indentUnit: 4,
		indentWithTabs: true,
		lineWrapping: true
	});//@ts-ignore
	const compile_output : HTMLTextAreaElement = document.getElementById('compile_output');
	function LockButtons(){
		compileButton.disabled = true;
		SaveButton.disabled = true;
	}
	function UnlockButtons(){
		compileButton.disabled = false;
		SaveButton.disabled = false;
	}
	compilatorSocket.onclose = function(e){
		console.error('Compilation socket closed unexpectedly');
		LockButtons();
	};
	compilatorSocket.onmessage = function(e){
		const data = JSON.parse(e.data);
		if(data.logdata) compile_output.value += data.logdata;
		if(data.unlock) UnlockButtons();
	};
	function savecode(code = code_editor.getValue()){
		setCookie('code', code, 365);
	}
	compileButton.onclick = function(e){
		compile_output.value = "";
		let code = code_editor.getValue();
		if(autosave.checked) savecode(code);
		LockButtons();
		compilatorSocket.send(JSON.stringify({'data_to_compile': code}));
	};
	SaveButton.onclick = function(e){
		savecode();
	};
	if(document.cookie){
		let code = getCookie('code');
		if(code)
			code_editor.setValue(code);
		let autosave_cookie = getCookie('autosave');
		if(autosave_cookie)
			autosave.checked = (autosave_cookie === 'true');
	}

	//@ts-ignore
	function handle_needsave(e){
		if(autosave.checked) savecode();
	}
	autosave.onchange = function(e){
		setCookie('autosave', autosave.checked ? 'true' : 'false', 365);
		if(autosave.checked)
			code_editor.on('change', handle_needsave);
		else
			code_editor.off('change', handle_needsave);
	}
	if(autosave.checked)
		code_editor.on('change', handle_needsave);

	// code_editor.addEventListener('keydown', function(e){
	//	if(e.ctrlKey)
	//		if(e.key === 'k'){
	//		    e.preventDefault();
	//		    compileButton.click();
	//		}
	//		if(e.key === 's'){
	//		    e.preventDefault();
	//		    SaveButton.click();
	//		}
	// });
});
