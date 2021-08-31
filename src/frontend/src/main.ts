import './style.css'
import './index.css'
import Cookies from 'js-cookie'

async function toggleReviewer() {
    const csrftoken = Cookies.get('csrftoken');
    // fetch('/')
    // this.assigned = ! this.assigned;
    await fetch(this.toggleUrl, {
        method: 'POST',
        headers: { "X-CSRFToken": csrftoken }
    }).then(response => response.json())
        .then(data => {
            console.log(data);
            this.isAssigned = data.isAssigned;
        })
}

window.toggleReviewer = toggleReviewer;