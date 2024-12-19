from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument
from pydantic import BaseModel
from uuid import uuid4

class ListSummary(BaseModel):
    id: str
    name: str
    item_count: int

    @staticmethod
    def from_document(document: dict) -> 'ListSummary':
        return ListSummary(
            id=str(document['_id']),
            name=document['name'],
            item_count=document['item_count'],
        )
    

class ToDoListItem(BaseModel):
    id: str
    label: str
    checked: bool

    @staticmethod
    def from_document(document: dict) -> 'ToDoListItem':
        return ToDoListItem(
            id=document['id'],
            label=document['label'],
            checked=document['checked'],
        )
    

class ToDoList(BaseModel):
    id: str
    name: str
    items: list[ToDoListItem]

    @staticmethod
    def from_document(document: dict) -> 'ToDoList':
        return ToDoList(
            id=str(document['_id']),
            name=document['name'],
            items=[ToDoListItem.from_document(item) for item in document['items']],
        )
    

class ToDoDAL:
    def __init__(self, todo_collection: AsyncIOMotorCollection):
        self._todo_collection = todo_collection
    
    async def list_todo_lists(self, session=None):
        async for doc in self._todo_collection.find(
            {},
            projection={
                "name": 1,
                "item_count": {"$size": "$items"},
            },
            sort={"name": 1},
            session=session,
        ):
            yield ToDoList.from_document(doc)

    async def create_todo_list(self, name: str, session=None) -> str:
        response = await self._todo_collection.insert_one(
            {"name": name, "items": []},
            session=session,
        )
        return str(response.inserted_id)
    
    async def get_todo_list(self, id: str | ObjectId, session=None) -> ToDoList:
        doc = await self._todo_collection.find_one(
            {"_id": ObjectId(id)},
            session=session,
        )
        if doc is None:
            raise ValueError(f"Todo list with id {id} not found")
        
        return ToDoList.from_document(doc)
    
    async def delete_todo_list(self, id: str | ObjectId, session=None) -> bool:
        result = await self._todo_list_collection.delete_one({"_id": ObjectId(id)}, session=session,)
        return result.deleted_count == 1
    
    async def create_item(self, id: str | ObjectId, label: str, session=None) -> ToDoList | None:
        result = await self._todo_collection.find_one_and_update()