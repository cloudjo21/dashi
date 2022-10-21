import axios from "axios";


// var tokens = []

function nuggetRequest() {
    // const url = 'http://hostname:31019/tagging?tagger_type=seunjeon&text=hello&use_inflect=false';
    const url = '/tagging';
    return axios.post(url);

    // const url = '/tagging?tagger_type=seunjeon&text=hello&use_inflect=false';
    // return axios.get(url);
}

// var body = {
//     "taggerType": "seunjeon",
//     "text": ["안녕하세요"],
//     "splitSentence": True,
//     "useInflect": False
// }
// const userAction = async () => {
//     const response = await fetch('http://hostname:31019/tagging/bulk', {
//       method: 'POST',
//       body: body, // string or object
//       headers: {
//         'Content-Type': 'application/json'
//       }
//     });
//     const myJson = await response.json(); //extract JSON from the http response
//     // do something with myJson
// }

// function nugget_request() {
//     return axios.post(
//         'http://hostname:31019/tagging/bulk', {

//         }
//     )
// }

export {nuggetRequest};
