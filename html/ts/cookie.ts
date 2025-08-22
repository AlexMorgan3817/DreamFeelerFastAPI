export const escaper = encodeURIComponent || escape;
export const decoder = decodeURIComponent || unescape;

export function setCookie(cname: string, cvalue: string, exdays: number): void {
    cvalue = escaper(cvalue);
    const d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    const expires = 'expires=' + d.toUTCString();
    document.cookie = cname + '=' + cvalue + '; ' + expires + "; path=/";
}

export function getCookie(cname: string): string {
    const name = cname + '=';
    const ca:string[] = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c:string = ca[i]!;
        while (c.charAt(0) == ' ')
			c = c.substring(1);
        if (c.indexOf(name) === 0) {
            return decoder(c.substring(name.length, c.length));
        }
    }
    return '';
}
