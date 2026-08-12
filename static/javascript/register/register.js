
function togglePassword(){
    const  passwordInput = document.getElementById('password');
    const eyeImage = document.getElementById('closeicon');

    if (passwordInput.type == "password") {
       passwordInput.type = 'text'
       eyeImage.src = 'static/images/open_eye.png'
    }else{
        passwordInput.type = 'password'
       eyeImage.src = 'static/images/close_eye.png'
    }
}

function confirmTogglePassword(){
    const  passwordInput = document.getElementById('confirmpassword');
    const eyeImage = document.getElementById('openicon');

    if (passwordInput.type == "password") {
       passwordInput.type = 'text'
       eyeImage.src = 'static/images/open_eye.png'
    }else{
        passwordInput.type = 'password'
       eyeImage.src = 'static/images/close_eye.png'
    }
}