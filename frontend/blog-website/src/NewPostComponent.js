import { useContext, useState } from "react";
import "./styles/NewPost.css"
import axios from 'axios';
import { AuthContext } from "./context/AuthProvider";
import { v4 as uuidv4 } from 'uuid';

const NewPostComponent = (params) => {
    const {auth, setAuth} = useContext(AuthContext);

    const [postName, setPostName] = useState("");
    const [postContent, setPostContent] = useState("");
    const [currentPicture, setCurrentPicture] = useState(null);
    const [images, setImages] = useState([]);
    const [sentDataToServer, setDataSendStatus] = useState("")

    console.log(auth)

    function PostNewPost(event) {
        const postData = async () => {
            const formData = new FormData();

            // Добавляем данные поста
            formData.append("author", auth["user"]["id"]);
            formData.append("postname", postName);
            formData.append("content", postContent);
    
            // Добавляем изображения
            images.forEach((image, index) => {
                formData.append(`image_${index}`, image);
            });
    
            try {
                console.log(params.api_url + "new_post")
                const response = await axios.post(params.api_url + "new_post", formData, {
                    headers: {
                        "Content-Type": "multipart/form-data"
                    }
                });
    
                console.log("Успешно:", response.data);
                setImages([]);
                setCurrentPicture(null);
                setPostName("");
                setPostContent("");
                setDataSendStatus("success")
            } catch (error) {
                console.error("Ошибка при отправке:", error);
                setDataSendStatus("fail")
            }
        }
        event.preventDefault()
        try
        {
            if (auth?.user)
            {
                postData()
            }
        }
        catch (e)
        {
            console.log(e);
            setDataSendStatus("fail")
        }
        return 0;
    }

    function AddPicture(event) {
        event.preventDefault()
        if (currentPicture != null)
        {
            setImages(images.concat(currentPicture))
            console.log(images);
        }
    }


    return ( 
        <>
            <div className="new-post-box">
                <form className="new-post-form" onSubmit={PostNewPost}>
                    <label htmlFor="PostNameInput"> Название: </label>
                    <input type="text" id="PostNameInput" placeholder="введите название поста" onChange={(e) => {setPostName(e.target.value)}} value={postName} required/>
                    <label htmlFor="PostContentInput"> Текст: </label>
                    <textarea type="text" id="PostContentInput" placeholder="о чем расскажете?" onChange={(e) => {setPostContent(e.target.value)}} value={postContent} required></textarea>
                    <label htmlFor="PostFileInput"> Прикрепите картинки </label>
                    <input id="PostFileInput" accept="image/*" type="file" multiple onChange={(e) => setCurrentPicture(e.target.files[0])} />
                    <button onClick={AddPicture}> Добавить картинку</button>
                    <br/>
                    {
                        images.map((item) => {
                            return (<div key={uuidv4()}>Картинка</div>)
                        })
                    }
                    <br/>
                    <button>Запостить</button>
                </form>
            </div>
        </>
     );
}
 
export default NewPostComponent;