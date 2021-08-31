import './style.css'
import './index.css'
import Cookies from 'js-cookie'

async function toggleReviewer(this: any) {
    const csrftoken = Cookies.get('csrftoken');

    await fetch(this.toggleUrl, {
        method: 'POST',
        // @ts-ignore
        headers: {"X-CSRFToken": csrftoken}
    }).then(response => response.json())
        .then(data => {
            this.isAssigned = data.isAssigned;
        })
}

(window as any).toggleReviewer = toggleReviewer;